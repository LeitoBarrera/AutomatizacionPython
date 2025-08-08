# consulta/eu_fin_sanctions.py
import os, time, re
from playwright.sync_api import sync_playwright

URL = ("https://data.europa.eu/data/datasets/"
       "consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions?locale=en")

def _click_cookies(page):
    # intentos típicos de banner de cookies
    selectors = [
        "button:has-text('Accept all cookies')",
        "button:has-text('Accept only essential cookies')",
        "button#onetrust-accept-btn-handler",
        "button:has-text('Accept cookies')",
    ]
    for sel in selectors:
        try:
            page.locator(sel).first.click(timeout=1500)
            return True
        except Exception:
            pass
    return False

def consultar_eu_fin_sanctions(nombre_completo: str, folder: str):
    """
    Abre el dataset 'EU financial sanctions' en data.europa.eu,
    escribe el nombre en el buscador, lanza la búsqueda, espera resultados
    y toma un pantallazo (solo primera página).
    Devuelve la ruta del PNG.
    """
    os.makedirs(folder, exist_ok=True)
    safe = (nombre_completo or "consulta").strip()
    safe = re.sub(r"\s+", "_", safe)
    out_path = os.path.join(folder, f"eu_fin_sanctions_{safe}.png")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            locale="en-US",
        )
        page = context.new_page()

        # Ir a la página
        page.goto(URL, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        # Cookies (best-effort)
        _click_cookies(page)

        # Localizar input y botón (los data-v-* cambian, usamos clases estables)
        # input.search-input  +  button.search-button
        page.wait_for_selector("input.search-input", timeout=15000)
        page.fill("input.search-input", nombre_completo or "")
        # A veces hace falta un pequeño delay para que reactive el botón
        page.wait_for_timeout(300)
        page.locator("button.search-button").click()

        # La página tarda en montar resultados. Dales tiempo.
        # Intentar esperar por un contenedor de resultados y, en todo caso, fallback a dormir 10s
        waited = False
        for sel in [
            ".results",                # contenedor genérico
            ".result",                 # item genérico
            "[class*='result']",
            "section:has-text('Results')",
        ]:
            try:
                page.locator(sel).first.wait_for(state="visible", timeout=8000)
                waited = True
                break
            except Exception:
                continue
        if not waited:
            page.wait_for_timeout(10000)  # fallback explícito que pediste (~10s)

        # Por si hay lazy-loading, un pequeño scroll para forzar render
        try:
            page.mouse.wheel(0, 800)
            page.wait_for_timeout(300)
        except Exception:
            pass

        # Pantallazo de la primera página de resultados
        page.screenshot(path=out_path, full_page=True)

        browser.close()

    return out_path
