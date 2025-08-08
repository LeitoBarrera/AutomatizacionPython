# consulta/eu_sanctions_tracker.py
import os, re, time
from playwright.sync_api import sync_playwright

URL = "https://data.europa.eu/apps/eusanctionstracker/"

def _accept_cookies(page):
    for sel in [
        "button:has-text('I accept cookies')",
        "button:has-text('Accept all cookies')",
        "button#onetrust-accept-btn-handler",
        "button:has-text('I accept')",
    ]:
        try:
            page.locator(sel).first.click(timeout=1500)
            return True
        except Exception:
            pass
    return False

def consultar_eu_sanctions_tracker(nombre_completo: str, folder: str) -> str:
    """
    Busca 'nombre_completo' en EU sanctions tracker.
    - Si no hay resultados, pantallazo de 'No results found'.
    - Si hay resultados, abre el primero y guarda pantallazo.
    Devuelve la ruta del PNG.
    """
    os.makedirs(folder, exist_ok=True)
    safe = re.sub(r"\s+", "_", (nombre_completo or "consulta").strip()) or "consulta"
    out_path = os.path.join(folder, f"eu_sanctions_tracker_{safe}.png")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1400, "height": 900}, locale="en-US")
        page = context.new_page()

        page.goto(URL, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass

        _accept_cookies(page)

        # ----- LOCALIZAR Y ESCRIBIR EN EL COMBOBOX (Tom Select) -----
        # 1) Por rol accesible (más estable aquí)
        try:
            inp = page.get_by_role("combobox", name=re.compile(r"Search sanctions", re.I))
            inp.wait_for(state="visible", timeout=10000)
        except Exception:
            # 2) Fallbacks por cambios de DOM
            inp = None
            for s in [
                "div#search-field-ts-control input",
                "input#search-field",
                "input[role='combobox']",
                "input[aria-autocomplete='list']",
            ]:
                loc = page.locator(s).first
                if loc.count():
                    inp = loc
                    break
            if inp is None:
                page.screenshot(path=out_path, full_page=True)
                browser.close()
                raise RuntimeError("No pude encontrar el campo de búsqueda del tracker.")

        # Dar foco y escribir (Tom Select a veces ignora .fill(); mejor .type)
        inp.click()
        try:
            inp.fill("")  # limpia cualquier texto previo si permite fill
        except Exception:
            pass

        query = (nombre_completo or "").strip()
        inp.type(query, delay=50)
        page.wait_for_timeout(500)

        # Asegurar que el valor quedó y disparar evento input si no
        try:
            if query and (inp.input_value() or "").strip() == "":
                el = inp.element_handle()
                page.evaluate(
                    """(el, val) => { el.value = val; el.dispatchEvent(new Event('input', {bubbles:true})); }""",
                    el, query
                )
        except Exception:
            pass

        # Espera a que el dropdown de sugerencias aparezca (si hay)
        try:
            page.locator(".ts-dropdown").wait_for(state="visible", timeout=8000)
        except Exception:
            pass

        # ----- MANEJO DE RESULTADOS -----
        # Caso 1: No hay resultados (texto del componente)
        try:
            nores = page.locator(".ts-dropdown:has-text('No results found')")
            if nores.is_visible():
                page.screenshot(path=out_path, full_page=True)
                browser.close()
                return out_path
        except Exception:
            pass

                # Caso 2: Hay opciones -> entra al primero
        first_opt = page.locator(".ts-dropdown .option").first
        if first_opt.count() > 0:
            first_opt.click()

            # Esperar que aparezca el nombre en el detalle
            try:
                page.wait_for_selector(
                    "h1, h2, .profile, .details, [role='main']",
                    timeout=12000
                )
            except Exception:
                page.wait_for_timeout(3000)

            # Esperar contenido adicional (gráficos/tablas)
            try:
                page.wait_for_selector(
                    ".chart, table, .dataTables_wrapper, .related-entities",
                    timeout=8000
                )
            except Exception:
                pass

            # Tiempo extra para asegurar render completo
            page.wait_for_timeout(2500)

            # Scroll suave para pintar todo
            try:
                page.mouse.wheel(0, 1500)
                page.wait_for_timeout(500)
            except Exception:
                pass

            page.screenshot(path=out_path, full_page=True)

        else:
            # Fallback: Enter por si abre listado, y capturar
            try:
                inp.press("Enter")
                page.wait_for_timeout(4000)
            except Exception:
                pass
            page.screenshot(path=out_path, full_page=True)

        browser.close()
    return out_path
