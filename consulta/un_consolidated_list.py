# consulta/un_consolidated_list.py
import os, re, time
from playwright.sync_api import sync_playwright

URL = "https://main.un.org/securitycouncil/es/content/un-sc-consolidated-list"

def _accept_cookies(page):
    # Botones típicos (ES/EN) + OneTrust
    for sel in [
        "button:has-text('Acepto las cookies')",
        "button:has-text('Accept all cookies')",
        "button#onetrust-accept-btn-handler",
        "button:has-text('I accept')",
        "button:has-text('Aceptar')",
    ]:
        try:
            page.locator(sel).first.click(timeout=1500)
            return True
        except Exception:
            pass
    return False

def consultar_un_consolidated_list(nombre_completo: str, folder: str) -> str:
    """
    Abre la página de la lista consolidada del CSNU (ES), despliega el buscador,
    busca por nombre y toma un pantallazo de la primera página de resultados.
    Devuelve la ruta del PNG.
    """
    os.makedirs(folder, exist_ok=True)
    safe = re.sub(r"\s+", "_", (nombre_completo or "consulta").strip()) or "consulta"
    out_path = os.path.join(folder, f"un_consolidated_{safe}.png")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            locale="es-ES",
        )
        page = context.new_page()

        # 1) Ir al sitio
        page.goto(URL, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        # 2) Cookies (si salen)
        _accept_cookies(page)

        # 3) Abrir el buscador (toggler)
        #   Usamos una selección robusta: por clase base y por data-bs-target.
        toggler = page.locator(
            "button.search-toggler, button[data-bs-target*='block-simple-search-form']"
        ).first
        try:
            toggler.wait_for(state="visible", timeout=8000)
            toggler.click()
        except Exception:
            # Si ya está abierto o el selector cambia, seguimos
            pass

        # 4) Localizar input y botón de búsqueda
        #    IDs que viste en la inspección (#edit-p--2 y #edit-submit--2),
        #    más un fallback por placeholder/clase si cambian el sufijo --2.
        inp = page.locator("#edit-p--2").first
        if inp.count() == 0:
            inp = page.locator("input.block-serach.form-search.form-control").first
        if inp.count() == 0:
            inp = page.locator("input[placeholder*='Busca algo']").first

        btn = page.locator("#edit-submit--2").first
        if btn.count() == 0:
            btn = page.locator("button[type='submit']:has-text('Buscar'), button[title*='Buscar']").first

        # 5) Escribir y lanzar la búsqueda
        inp.wait_for(state="visible", timeout=10000)
        inp.click()
        inp.fill(nombre_completo or "")
        page.wait_for_timeout(300)


       # Después de hacer click en el botón o Enter:
        try:
            if btn.count() > 0:
                btn.click()
            else:
                inp.press("Enter")
        except Exception:
            try:
                inp.press("Enter")
            except Exception:
                pass

        # ⏳ Espera fija de 2-3 segundos antes de buscar los selectores de resultados
        page.wait_for_timeout(3000)

        # Luego la espera normal de carga
        try:
            page.wait_for_load_state("networkidle", timeout=12000)
        except Exception:
            pass


        # Señales de resultados (bloques de búsqueda o listados)
        try:
            page.wait_for_selector(
                ".view, .search-results, .region-content, main, article, .views-row",
                timeout=12000
            )
        except Exception:
            # Igual tomamos captura por si el texto "No se encontraron resultados" ya está visible
            pass

        # 7) Screenshot
        #    Pequeño scroll para que se pinten gráficos/imágenes si los hay
        try:
            page.mouse.wheel(0, 600)
            page.wait_for_timeout(300)
        except Exception:
            pass

        page.screenshot(path=out_path, full_page=True)
        browser.close()

    return out_path
