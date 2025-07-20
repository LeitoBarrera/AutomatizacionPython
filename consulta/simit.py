from playwright.sync_api import sync_playwright
import time

def consultar(cedula, folder):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://fcm.org.co/simit/#/consultaComparendos')
        page.fill('input[formcontrolname="numeroIdentificacion"]', cedula)
        page.click('button[type="submit"]')
        time.sleep(5)
        page.screenshot(path=f'{folder}/simit.png', full_page=True)
        browser.close()