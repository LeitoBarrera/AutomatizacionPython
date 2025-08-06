from playwright.sync_api import sync_playwright
import time
import os

def consultar_offshore(nombre_completo, folder):
    resultados = []
    archivo_base = os.path.join(folder, "offshore")

    with sync_playwright() as p:
        # 1. Abrimos navegador en modo no-headless para evitar bloqueos
        browser = p.chromium.launch(headless=False)  # <-- importante
        context = browser.new_context()
        page = context.new_page()

        print("[INFO] Abriendo Offshore Leaks...")
        page.goto("https://offshoreleaks.icij.org/", wait_until="networkidle")

        # 2. Esperar el popup y aceptar términos
        try:
            page.wait_for_selector('input#accept', timeout=8000)
            page.check('input#accept')  # más fiable que click
            page.click('button.btn.btn-primary.btn-block.btn-lg')
            print("[INFO] Popup aceptado correctamente.")
            page.wait_for_timeout(2000)
        except:
            print("[WARN] No apareció el popup de aceptación, continuando...")

        # 3. Buscar la barra de búsqueda y escribir el nombre
        page.wait_for_selector('input[name="q"]', timeout=15000)
        page.fill('input[name="q"]', nombre_completo)
        page.keyboard.press("Enter")
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        # 4. Capturar hasta 3 páginas de resultados
        for i in range(1, 4):
            screenshot_path = f"{archivo_base}_page{i}.png"
            page.screenshot(path=screenshot_path, full_page=True)
            resultados.append(screenshot_path)

            # Intentar ir a la siguiente página
            next_button = page.locator('a.page-link[aria-label="Next »"]')
            if next_button.count() > 0 and next_button.is_enabled():
                next_button.click()
                page.wait_for_load_state("networkidle")
                time.sleep(3)
            else:
                break

        browser.close()

    return resultados
