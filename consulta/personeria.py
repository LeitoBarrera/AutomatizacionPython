from playwright.sync_api import sync_playwright
import time

def consultar(cedula, folder):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://www.personeriabogota.gov.co/sdqp/antecedentes')
        page.fill('input[name="cedula"]', cedula)
        page.click('button[type="submit"]')
        time.sleep(5)
        page.screenshot(path=f'{folder}/personeria.png', full_page=True)
        browser.close()