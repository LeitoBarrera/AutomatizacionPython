# consulta/ofsi_sanctions_pdf.py
import os, re, time
from playwright.sync_api import sync_playwright

URL = "https://sanctionssearchapp.ofsi.hmtreasury.gov.uk/"

def consultar_ofsi_pdf(nombre_completo: str, folder: str) -> str:
    """
    Busca 'nombre_completo' en el buscador de OFSI y exporta los resultados a PDF.
    NOTA: page.pdf() requiere Chromium en modo headless.
    Devuelve la ruta del PDF generado.
    """
    os.makedirs(folder, exist_ok=True)
    safe = re.sub(r"\s+", "_", (nombre_completo or "consulta").strip()) or "consulta"
    out_pdf = os.path.join(folder, f"ofsi_results_{safe}.pdf")

    with sync_playwright() as p:
        # PDF sólo funciona en headless en Chromium
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale="en-GB", viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1) Abrir sitio
        page.goto(URL, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        # 2) Llenar el campo y buscar
        page.locator("#txtSearch").wait_for(state="visible", timeout=10000)
        page.fill("#txtSearch", nombre_completo or "")
        page.click("#btnSearch")

        # 3) Esperar resultados (el sitio puede tardar un poco)
        #    Intentamos varios selectores razonables; si no, hacemos fallback con un sleep corto.
        waited = False
        for sel in [
            "table", 
            "tbody tr", 
            "text=Search results", 
            ".table-responsive", 
            "app-results"
        ]:
            try:
                page.wait_for_selector(sel, timeout=12000)
                waited = True
                break
            except Exception:
                continue
        if not waited:
            page.wait_for_timeout(3000)

        # 4) Preparar para imprimir y generar PDF (con fondos y márgenes decentes)
        try:
            page.emulate_media(media="print")
        except Exception:
            pass

        page.pdf(
            path=out_pdf,
            format="A4",
            print_background=True,
            margin={"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"},
        )

        browser.close()

    return out_pdf
