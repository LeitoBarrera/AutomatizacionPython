import os
import time
from playwright.sync_api import sync_playwright

def consultar_fbi_news(nombre, folder):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("[INFO] Abriendo FBI News Stories...")
        page.goto("https://www.fbi.gov/news/stories", timeout=120000)

        # Esperar input de filtro
        page.wait_for_selector('#filter-input', timeout=60000)

        print(f"[INFO] Buscando: {nombre}")
        page.fill('#filter-input', nombre)
        time.sleep(1)  # Pequeña pausa para que el DOM procese

        # Simular Enter para aplicar el filtro
        page.keyboard.press("Enter")
        print("[INFO] Enter presionado para filtrar resultados")

        # Esperar que carguen los resultados
        time.sleep(4)

        # Guardar screenshot
        os.makedirs(folder, exist_ok=True)
        filename = f"fbi_news_{nombre.replace(' ', '_')}.png"
        screenshot_path = os.path.join(folder, filename)
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"[INFO] Captura guardada en: {screenshot_path}")

        browser.close()
        return screenshot_path
