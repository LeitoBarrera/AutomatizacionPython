# consulta/eu_taric.py
from playwright.sync_api import sync_playwright
import os
import time

URL = "https://ec.europa.eu/taxation_customs/dds2/taric/taric_consultation.jsp?Lang=en"

def consultar_eu_taric(nombre_completo, folder):
    """
    Abre TARIC (Chromium), busca por 'nombre_completo' en #search-input-id,
    hace submit y guarda UNA captura PNG de la primera página de resultados.
    Retorna la ruta del PNG.
    """
    os.makedirs(folder, exist_ok=True)
    safe = (nombre_completo or "consulta").strip().replace(" ", "_")
    out_path = os.path.join(folder, f"eu_taric_{safe}.png")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("[TARIC] Abriendo sitio…")
        page.goto(URL, wait_until="networkidle")

        # Cookies (varían, probamos varios textos comunes del ECL)
        for sel in [
            "button:has-text('Accept all cookies')",
            "button:has-text('I accept')",
            "button#accept-all-cookies",
            "button.ecl-button--primary:has-text('Accept')",
        ]:
            try:
                page.locator(sel).first.click(timeout=1500)
                break
            except:
                pass

        # Input + submit
        page.wait_for_selector("#search-input-id", timeout=15000)
        page.fill("#search-input-id", nombre_completo)

        # Botón Search (aria-label)
        page.locator('button[aria-label="Search"]').first.click()

        # Espera a que pinten resultados o a que la red quede estable
        try:
            # Contenedor típico del contenido/resultados
            page.wait_for_selector("main, section#content, div.results", timeout=15000)
        except:
            pass
        page.wait_for_load_state("networkidle")
        time.sleep(1.2)  # pequeño settle

        # Captura de la PRIMERA página únicamente
        page.screenshot(path=out_path, full_page=True)
        print(f"[TARIC] Captura guardada: {out_path}")

        browser.close()

    return out_path
