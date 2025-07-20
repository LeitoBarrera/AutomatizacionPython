from playwright.sync_api import sync_playwright
import time

def consultar(cedula, folder):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # HEADLESS FALSE PARA CAPTCHA
        page = browser.new_page()
        page.goto('https://antecedentes.policia.gov.co:7005/WebJudicial/')
        page.fill('input[name="nuip"]', cedula)
        input("\nResuelve el CAPTCHA manualmente y presiona Enter para continuar...")
        page.click('input[name="btnConsultar"]')
        time.sleep(5)
        page.screenshot(path=f'{folder}/policia_nacional.png', full_page=True)
        browser.close()