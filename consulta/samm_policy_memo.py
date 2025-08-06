import os
from playwright.sync_api import sync_playwright

def consultar_samm_policy_memo(nombre_completo, folder):
    """Consulta en SAMM DSCA Policy Memo y guarda una captura de pantalla de los resultados"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("[INFO] Abriendo SAMM DSCA Policy Memo...")
        page.goto("https://samm.dsca.mil/search/policy_memo", timeout=60000)

        # Esperar el campo de búsqueda
        page.wait_for_selector('#edit-search-api-fulltext', timeout=20000)

        # Escribir nombre completo
        page.fill('#edit-search-api-fulltext', nombre_completo)
        print(f"[INFO] Buscando en Policy Memo: {nombre_completo}")

        # Hacer clic en buscar
        page.click('#edit-submit-search-view-all-site-content')

        # Esperar un tiempo fijo para que cargue la página
        page.wait_for_timeout(5000)

        # Guardar captura de pantalla de toda la página
        os.makedirs(folder, exist_ok=True)
        screenshot_path = os.path.join(folder, f'samm_policy_memo_{nombre_completo.replace(" ", "_")}.png')
        page.screenshot(path=screenshot_path, full_page=True)

        print(f"[INFO] Captura guardada en: {screenshot_path}")
        browser.close()
        return screenshot_path
