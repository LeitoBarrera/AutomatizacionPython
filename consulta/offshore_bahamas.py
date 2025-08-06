from playwright.sync_api import sync_playwright
import os
import time

def consultar_offshore_bahamas(nombre_completo, folder):
    resultados = []
    archivo_base = os.path.join(folder, "offshore_bahamas")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("[INFO] Abriendo Bahamas Leaks...")
        page.goto("https://offshoreleaks.icij.org/investigations/bahamas-leaks", wait_until="networkidle")

        try:
            page.wait_for_selector('input#accept', timeout=6000)
            page.check('input#accept')
            page.click('button.btn.btn-primary.btn-block.btn-lg')
            time.sleep(2)
            print("[INFO] Popup aceptado.")
        except:
            print("[INFO] No apareció el popup de aceptación.")

        page.wait_for_selector('input[name="q"]', timeout=10000)
        page.fill('input[name="q"]', nombre_completo)
        page.keyboard.press("Enter")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        for i in range(1, 4):
            screenshot_path = f"{archivo_base}_page{i}.png"
            page.screenshot(path=screenshot_path, full_page=True)
            resultados.append(screenshot_path)
            print(f"[INFO] Captura guardada: {screenshot_path}")

            next_button = page.locator('a.page-link[aria-label="Next »"]')
            if next_button.count() and next_button.is_enabled():
                next_button.click()
                page.wait_for_load_state("networkidle")
                time.sleep(2)
            else:
                break

        browser.close()
    return resultados
