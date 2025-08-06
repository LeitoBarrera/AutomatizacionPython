# registraduria.py
import os
from playwright.sync_api import sync_playwright

def consultar_registraduria(nuip):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("[INFO] Abriendo Registraduría...")
        page.goto("https://consultasrc.registraduria.gov.co/ProyectoSCCRC/", timeout=120000)

        # Paso 1: Click en "Inicio de sesión de usuario público"
        page.wait_for_selector('#controlador\\:consultasId', timeout=60000)
        page.click('#controlador\\:consultasId')
        print("[INFO] Sesión pública abierta.")

        # Paso 2: Seleccionar tipo de búsqueda
        page.wait_for_selector('#searchForm\\:tiposBusqueda', timeout=60000)
        page.select_option('#searchForm\\:tiposBusqueda', label="DOCUMENTO (NUIP/NIP/Tarjeta de Identidad)")

        # Paso 3: Llenar número de documento
        page.wait_for_selector('#searchForm\\:documento', timeout=60000)
        page.fill('#searchForm\\:documento', nuip)

        # Paso 4: Captura de captcha
        page.wait_for_selector('img[src*="kaptcha.jpg"]', timeout=60000)
        captcha_element = page.query_selector('img[src*="kaptcha.jpg"]')

        os.makedirs("downloads", exist_ok=True)
        captcha_path = os.path.join("downloads", f"registraduria_captcha_{nuip}.png")
        captcha_element.screenshot(path=captcha_path)
        print(f"[INFO] Captura de captcha guardada en: {captcha_path}")

        # Abrir imagen automáticamente
        os.system(f'start {captcha_path}' if os.name == 'nt' else f'xdg-open {captcha_path}')
        captcha_text = input("[INPUT] Ingrese el captcha de la Registraduría: ").strip()

        # Paso 5: Llenar captcha
        page.wait_for_selector('input[id="searchForm:inCaptcha"]', timeout=60000)
        page.fill('input[id="searchForm:inCaptcha"]', captcha_text)

        # Paso 6: Clic en botón de búsqueda
        page.wait_for_selector('#searchForm\\:busquedaRCX', timeout=60000)
        page.click('#searchForm\\:busquedaRCX')
        print("[INFO] Enviando consulta...")

        # Paso 7: Esperar los resultados
        page.wait_for_selector('#j_idt6\\:documento', timeout=60000)

        # Paso 8: Extraer datos
        datos = {
            "cedula": page.locator('#j_idt6\\:documento').inner_text(),
            "primer_apellido": page.locator('#j_idt6\\:primerApellido').inner_text(),
            "segundo_apellido": page.locator('#j_idt6\\:segundoApellido').inner_text(),
            "primer_nombre": page.locator('#j_idt6\\:primerNombre').inner_text(),
            "segundo_nombre": page.locator('#j_idt6\\:segundoNombre').inner_text(),
            "sexo": page.locator('#j_idt6\\:sexo').inner_text()
        }

        print("[INFO] Datos obtenidos:", datos)

        browser.close()
        return datos
