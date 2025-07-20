from playwright.sync_api import sync_playwright
import time

def consultar(cedula, folder):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://www.runt.com.co/consultaCiudadana/#/consulta')
        page.fill('#numeroDocumento', cedula)
        page.select_option('#tipoDocumento', '1')
        page.click('#btnConsultar')
        time.sleep(5)
        page.screenshot(path=f'{folder}/runt.png', full_page=True)
        browser.close()