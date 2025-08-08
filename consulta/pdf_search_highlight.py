# consulta/pdf_search_highlight.py
import os
import re
import unicodedata
import fitz  # PyMuPDF

def _normalize(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.lower().strip()

def _tokenize(q: str):
    # tokens de 3+ letras (quita signos y múltiple espacio)
    return [t for t in re.split(r"\W+", _normalize(q)) if len(t) >= 3]

def buscar_en_pdf_y_resaltar(
    pdf_path: str,
    query: str,
    out_folder: str,
    export_first_if_none: bool = True,
    dpi: int = 150,
    stop_on_first: bool = False,   # corta en la primera página con match
    page_limit: int | None = None  # limitar páginas para pruebas / performance
):
    """
    Busca 'query' en pdf_path de forma tolerante (sin acentos, case-insensitive y
    permitiendo variaciones de espacios). Si no hay match exacto del nombre completo,
    busca por tokens (nombres/apellidos) y resalta lo encontrado.
    Exporta PNGs con annots=True. Si no hay matches, exporta la página 1 como preview.
    Retorna lista de PNGs generados.
    """
    os.makedirs(out_folder, exist_ok=True)
    resultados = []

    # Preparación de consulta
    q_norm = _normalize(query)
    tokens = _tokenize(query)
    # Patrón tolerante para "nombre completo": reemplaza espacios por \s+ y permite guiones
    full_pat = re.compile(r"\b" + re.sub(r"\s+", r"[\s\-]+", re.escape(q_norm)) + r"\b", re.IGNORECASE)

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"[PDF] Error abriendo PDF: {e}")
        return resultados

    total_pages = len(doc)
    print(f"[PDF] Abierto {pdf_path} con {total_pages} páginas")

    # Flags de PyMuPDF para search_for (si existen en tu versión)
    flags = 0
    for name in ("TEXT_IGNORECASE", "TEXT_DEHYPHENATE", "TEXT_PRESERVELIGATURES"):
        val = getattr(fitz, name, None)
        if isinstance(val, int):
            flags |= val

    last_page = total_pages if page_limit is None else min(page_limit, total_pages)
    hits_total = 0

    for i in range(last_page):
        page = doc[i]

        # 1) Intento de match del NOMBRE COMPLETO mediante texto plano normalizado
        page_text = page.get_text("text") or ""
        page_text_norm = _normalize(page_text)

        full_match_found = False
        if q_norm:
            if full_pat.search(page_text_norm):
                full_match_found = True

        rects = []

        if full_match_found:
            # Intentamos resaltar usando search_for del string original (puede fallar por acentos/espacios)
            # Si no encuentra, caemos a tokens para al menos resaltar partes.
            r_full = page.search_for(query, hit_max=200, quads=False, flags=flags) if query else []
            if not r_full:
                # Usa versión "espaciada": reemplaza espacios por simples
                q_simple = re.sub(r"\s+", " ", query.strip())
                r_full = page.search_for(q_simple, hit_max=200, quads=False, flags=flags)
            rects.extend(r_full)

        # 2) Si no hubo rects del nombre completo, buscamos por TOKENS (apellidos/nombres)
        if not rects and tokens:
            for tok in tokens:
                # Intentar resaltar cada token por separado
                r_tok = page.search_for(tok, hit_max=200, quads=False, flags=flags)
                # Si no encuentra (por acentos), prueba con el token original en mayúsc/minúsc
                if not r_tok and tok != tok.title():
                    r_tok = page.search_for(tok.title(), hit_max=200, quads=False, flags=flags)
                if r_tok:
                    rects.extend(r_tok)

        if rects:
            print(f"[PDF] Match en página {i+1}: {len(rects)} hits")
            hits_total += len(rects)
            for r in rects:
                try:
                    page.add_highlight_annot(r)
                except Exception:
                    pass

            # Render con anotaciones visibles
            pix = page.get_pixmap(dpi=dpi, annots=True)
            base = os.path.splitext(os.path.basename(pdf_path))[0]
            out_png = os.path.join(out_folder, f"{base}_match_p{i+1}.png")
            pix.save(out_png)
            resultados.append(out_png)

            if stop_on_first:
                break
        else:
            # Solo para feedback ocasional
            if (i + 1) % 50 == 0 or i in (0, 1):
                print(f"[PDF] Página {i+1} sin match...")

    if hits_total == 0 and export_first_if_none and total_pages > 0:
        print("[PDF] Sin coincidencias, exportando preview de la p.1")
        pix0 = doc[0].get_pixmap(dpi=dpi, annots=True)
        base = os.path.splitext(os.path.basename(pdf_path))[0]
        out_png0 = os.path.join(out_folder, f"{base}_p1_preview.png")
        pix0.save(out_png0)
        resultados.append(out_png0)

    doc.close()
    return resultados
