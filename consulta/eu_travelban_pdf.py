# consulta/eu_travelban_pdf.py
from playwright.sync_api import sync_playwright
import os
import re
import time
from urllib.parse import urlparse

URL = "https://www.sanctionsmap.eu/#/main/travel/ban"

def _content_disposition_filename(cd: str) -> str | None:
    # intenta extraer filename="...pdf" del header
    if not cd:
        return None
    m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^\";]+)"?', cd, flags=re.IGNORECASE)
    return m.group(1) if m else None

def consultar_eu_travelban_pdf(nombre_completo, folder):
    """
    Obtiene el HREF del enlace 'PDF' y descarga el archivo directamente con context.request.get().
    Devuelve la ruta local del PDF.
    """
    os.makedirs(folder, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        # usamos un context normal, pero descargamos vía context.request (no download API)
        context = browser.new_context()
        page = context.new_page()

        page.goto(URL, wait_until="networkidle")

        # cerrar/aceptar cookies si aparecen (best-effort)
        for sel in [
            "button:has-text('Accept all cookies')",
            "button:has-text('I accept')",
            "button:has-text('Accept')",
            "button#accept-all-cookies",
        ]:
            try:
                page.locator(sel).first.click(timeout=1200)
                break
            except:
                pass

        # abrir modal/info si es necesario
        try:
            page.locator("button[aria-label*='info'], button:has-text('Info')").first.click(timeout=1500)
            time.sleep(0.5)
        except:
            pass

        # localizar explícitamente el link con texto PDF
        link = page.locator("a[target='_blank']:has-text('PDF')").first
        link.wait_for(state="visible", timeout=10000)
        href = link.get_attribute("href")
        if not href:
            browser.close()
            raise RuntimeError("No se pudo obtener el href del enlace PDF.")

        # descarga directa por HTTP usando el request del context (hereda cookies)
        resp = context.request.get(href, headers={"Accept": "application/pdf"})
        if not resp.ok:
            browser.close()
            raise RuntimeError(f"Fallo al descargar PDF ({resp.status}): {href}")

        # determinar nombre de archivo
        cd = resp.headers.get("content-disposition") or resp.headers.get("Content-Disposition")
        filename = _content_disposition_filename(cd)
        if not filename:
            # fallback: nombre desde la URL
            parsed = urlparse(href)
            base = os.path.basename(parsed.path) or "TravelBans.pdf"
            # si viene sin .pdf, se lo ponemos
            if not base.lower().endswith(".pdf"):
                base = base + ".pdf"
            filename = base

        # aseguramos extensión
        if not filename.lower().endswith(".pdf"):
            filename = re.sub(r"\.[a-z0-9]+$", "", filename, flags=re.IGNORECASE) + ".pdf"

        out_path = os.path.join(folder, filename)
        with open(out_path, "wb") as f:
            f.write(resp.body())

        browser.close()
    return out_path
