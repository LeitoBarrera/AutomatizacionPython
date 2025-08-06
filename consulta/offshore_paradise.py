from playwright.sync_api import sync_playwright
import time
import os

def consultar_offshore_paradise(nombre_completo, folder):
    resultados = []
    archivo_base = os.path.join(folder, "offshore_paradise")

    with sync_playwright() as p:
        # Modo visible para evitar bloqueos
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("[INFO] Abriendo Paradise Papers...")
        page.goto("https://offshoreleaks.icij.org/investigations/paradise-papers", wait_until="networkidle")

        # 1. Esperar popup y aceptar términos (si aparece)
        try:
            page.wait_for_selector('input#accept', timeout=6000)
            page.check('input#accept')
            page.click('button.btn.btn-primary.btn-block.btn-lg')
            print("[INFO] Popup aceptado correctamente.")
            time.sleep(2)
        except:
            print("[WARN] No apareció el popup de aceptación.")

        # 2. Buscar la barra de búsqueda y escribir el nombre
        page.wait_for_selector('input[name="q"]', timeout=10000)
        page.fill('input[name="q"]', nombre_completo)
        page.keyboard.press("Enter")  # Simula submit
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        # 3. Capturar hasta 3 páginas de resultados
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
