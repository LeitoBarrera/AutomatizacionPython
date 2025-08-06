import os
from playwright.sync_api import sync_playwright

def consultar_samm(nombre_completo, folder):
    """Consulta en SAMM DSCA y guarda una captura de pantalla de los resultados"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("[INFO] Abriendo SAMM DSCA...")
        page.goto("https://samm.dsca.mil/search/site_search", timeout=60000)

        # Esperar el campo de búsqueda
        page.wait_for_selector('#edit-search-api-fulltext', timeout=20000)

        # Escribir nombre completo
        page.fill('#edit-search-api-fulltext', nombre_completo)
        print(f"[INFO] Buscando: {nombre_completo}")

        # Hacer clic en buscar
        page.click('#edit-submit-search-view-all-site-content')

        # Esperar 5 segundos para que cargue el contenido dinámico
        page.wait_for_timeout(5000)

        # Guardar captura de pantalla de toda la página
        os.makedirs(folder, exist_ok=True)
        screenshot_path = os.path.join(folder, f'samm_{nombre_completo.replace(" ", "_")}.png')
        page.screenshot(path=screenshot_path, full_page=True)

        print(f"[INFO] Captura guardada en: {screenshot_path}")
        browser.close()
        return screenshot_path
