from playwright.sync_api import sync_playwright
import os
import time

PAGE_TERMS = "https://antecedentes.policia.gov.co:7005/WebJudicial/"
PAGE_ANTE = "https://antecedentes.policia.gov.co:7005/WebJudicial/antecedentes.xhtml"

def consultar_policia_nacional(cedula, folder):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)  # slow_mo ayuda a no saturar la página
        context = browser.new_context()
        page = context.new_page()

        # Ir a la página de términos
        page.goto(PAGE_TERMS, timeout=60000)

        # Esperar checkbox de aceptación de términos
        page.wait_for_selector('#aceptaOption\\:0', timeout=15000)
        print("[INFO] Simulando lectura de términos...")
        page.wait_for_timeout(5000)  # 5 segundos de espera como si estuvieras leyendo

        # Marcar aceptar términos
        page.check('#aceptaOption\\:0')
        page.wait_for_timeout(2000)  # espera breve tras marcar

        # Click en el botón de continuar
        print("[INFO] Dando clic en continuar...")
        page.click('#continuarBtn')

        # Esperar que cargue la página de antecedentes
        page.wait_for_url(PAGE_ANTE, timeout=60000)
        print("[INFO] Página de antecedentes cargada.")

        # Simular lectura y llenado del formulario
        page.wait_for_timeout(3000)  # 3 segundos de espera

        # Completar formulario
        page.select_option('#cedulaTipo', 'cc')
        page.fill('#cedulaInput', cedula)
        print(f"[INFO] Documento {cedula} ingresado.")

        # Esperar manualmente para que puedas marcar captcha manual si deseas
        print("[INFO] Espera de 60 segundos para que resuelvas captcha manual y marques enviar.")
        page.wait_for_timeout(60000)

        # Intentar ubicar y hacer clic en el botón de enviar (forzar espera)
        try:
            print("[INFO] Intentando dar clic en botón enviar...")
            page.click('input[type="submit"]', timeout=20000)
        except Exception as e:
            print(f"[WARN] No se pudo hacer clic en el botón de enviar automáticamente: {e}")
            print("[INFO] Puedes dar clic manualmente en el botón y la ejecución continuará.")

        # Esperar a que cargue resultados
        print("[INFO] Esperando que carguen resultados...")
        page.wait_for_timeout(10000)

        # Capturar screenshot del resultado
        screenshot_path = f"{folder}/antecedentes_{cedula}.png"
        page.screenshot(path=screenshot_path)
        print(f"[INFO] Screenshot guardado en {screenshot_path}")

        browser.close()
        return screenshot_path

# Ejemplo de uso:
# consultar_policia_nacional("123456789", "./output")
