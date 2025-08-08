# consulta/interpol_red_notices.py
import os, re, time
from playwright.sync_api import sync_playwright

URL = "https://www.interpol.int/es/Como-trabajamos/Notificaciones/Notificaciones-rojas/Ver-las-notificaciones-rojas"

def consultar_interpol_red_notices(nombre_completo: str, folder: str) -> str:
    """
    Abre la página de Notificaciones Rojas de INTERPOL, abre el buscador,
    escribe 'nombre_completo', ejecuta la búsqueda, espera 2–3s y toma un pantallazo.
    Devuelve la ruta del PNG.
    """
    os.makedirs(folder, exist_ok=True)
    safe = re.sub(r"\s+", "_", (nombre_completo or "consulta").strip()) or "consulta"
    out_path = os.path.join(folder, f"interpol_red_notices_{safe}.png")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1400, "height": 900}, locale="es-ES")
        page = context.new_page()

        # 1) Cargar página
        page.goto(URL, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        # 2) Abrir el buscador (el botón/lupa del header)
        #    El toggle suele ser el div con clases: .search__toggle.js-toggleSearch
        #    Añadimos fallback por si cambia el DOM.
        togglers = [
            "div.search__toggle.js-toggleSearch",
            "button.js-toggleSearch",
            "button[aria-label*='Buscar']",
            "button[aria-label*='Search']",
            ".search__toggle"
        ]
        opened = False
        for sel in togglers:
            try:
                loc = page.locator(sel).first
                if loc.count():
                    loc.click(timeout=3000)
                    opened = True
                    break
            except Exception:
                continue

        # 3) Esperar el campo de texto del buscador y escribir
        #    input name="search" class="search__input"
        inp = page.locator("input.search__input[name='search']").first
        inp.wait_for(state="visible", timeout=10000)
        inp.click()
        inp.fill(nombre_completo or "")
        page.wait_for_timeout(200)  # mini pausa

        # 4) Click en la lupa del formulario (button.search__trigger)
        try:
            page.locator("button.search__trigger").first.click(timeout=4000)
        except Exception:
            # Fallback: Enter
            try:
                inp.press("Enter")
            except Exception:
                pass

        # 5) Darle tiempo a los resultados (2–3s como pediste)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        page.wait_for_timeout(2500)

        # 6) Pantallazo (full page para cubrir resultados o mensaje de “0 resultados”)
        page.screenshot(path=out_path, full_page=True)

        browser.close()
    return out_path
