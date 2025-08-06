import os
from playwright.sync_api import sync_playwright

PAGE_URL = "https://www.runt.gov.co/consultaCiudadana/#/consultaVehiculo"

MAP_TIPOS_RUNT = {
    "CC": "C",
    "TI": "T",
    "CE": "E",
    "PP": "P",
    "PTP": "PT",
    "PPT": "PP"
}

def consultar_runt(placa, documento, tipo_documento, folder):
    # Mapear tipo_doc del formulario al que entiende RUNT
    tipo_runt = MAP_TIPOS_RUNT.get(tipo_documento, "C")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("[INFO] Abriendo RUNT...")
        page.goto(PAGE_URL, timeout=60000)

        # Esperar campo de placa
        page.wait_for_selector('#noPlaca')
        page.fill('#noPlaca', placa)

        # Seleccionar tipo de documento
        page.select_option('#input-tipo-documento-automotores', tipo_runt)
        page.fill('#noDocumento', documento)

        # Esperar captcha y capturarlo
        page.wait_for_selector('#imgCaptcha')
        captcha_element = page.query_selector('#imgCaptcha')
        os.makedirs(folder, exist_ok=True)
        captcha_path = os.path.join(folder, "runt_captcha.png")
        captcha_element.screenshot(path=captcha_path)
        print(f"[INFO] Captura del captcha guardada en: {captcha_path}")

        # Mostrar captcha al usuario
        os.system(f'start {captcha_path}' if os.name == 'nt' else f'xdg-open {captcha_path}')
        solucion_captcha = input("[INPUT] Por favor ingresa el texto del captcha mostrado: ")

        # Llenar y enviar el captcha
        page.fill('#captchatxt', solucion_captcha)  
        page.click("button[type='submit']")

        # Esperar resultados y capturar pantalla
        page.wait_for_timeout(5000)
        screenshot_path = os.path.join(folder, f"runt_{documento}.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"[INFO] Screenshot guardado en: {screenshot_path}")

        browser.close()
        return screenshot_path
