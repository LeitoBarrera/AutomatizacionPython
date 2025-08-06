from playwright.sync_api import sync_playwright
import os

def consultar_offshore_panama(nombre_completo, folder):
    resultados = []
    archivo_base = os.path.join(folder, "offshore_panama")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://offshoreleaks.icij.org/investigations/panama-papers")

        # Intentar aceptar popup si aparece
        try:
            page.wait_for_selector('input#accept', timeout=5000)
            page.click('input#accept')
            page.click('button.btn.btn-primary.btn-block.btn-lg')
            page.wait_for_timeout(2000)
        except:
            print("No apareció el popup en Panama Papers, continuando...")

        # Buscar input de búsqueda
        page.wait_for_selector('input[name="q"]', timeout=10000)
        page.fill('input[name="q"]', nombre_completo)
        page.keyboard.press("Enter")
        page.wait_for_timeout(5000)

        # Capturar primeras 3 páginas de resultados
        for i in range(1, 4):
            screenshot_path = f"{archivo_base}_page{i}.png"
            page.screenshot(path=screenshot_path, full_page=True)
            resultados.append(screenshot_path)

            # Intentar ir a la siguiente página si existe
            next_button = page.locator('a.page-link[aria-label="Next »"]')
            if next_button.count() > 0 and next_button.is_enabled():
                next_button.click()
                page.wait_for_timeout(4000)
            else:
                break

        browser.close()

    return resultados
