import os
import time
from playwright.sync_api import sync_playwright

def consultar_samm_policy_memo(nombre, folder):
    """
    Busca el nombre en SAMM Policy Memo y guarda una captura de pantalla.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("[INFO] Abriendo SAMM DSCA Policy Memo...")
        page.goto("https://samm.dsca.mil/search/policy_memo", timeout=60000)

        # Esperar a que cargue el campo de búsqueda
        page.wait_for_selector("#edit-search-api-fulltext", timeout=20000)
        page.fill("#edit-search-api-fulltext", nombre)
        print(f"[INFO] Buscando en Policy Memo: {nombre}")

        # Click en el botón de buscar
        page.click("#edit-submit-search-view-policy-memo-content")

        # Espera para que carguen resultados y no salga en blanco
        time.sleep(5)

        # Crear carpeta si no existe
        os.makedirs(folder, exist_ok=True)
        screenshot_path = os.path.join(folder, f"samm_policy_memo_{nombre.replace(' ', '_')}.png")
        
        # Guardar captura de pantalla
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"[INFO] Captura guardada en: {screenshot_path}")

        browser.close()
        return screenshot_path
