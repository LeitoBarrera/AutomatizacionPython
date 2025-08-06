import os
import time
from playwright.sync_api import sync_playwright, TimeoutError

def consultar_simit(placa, folder):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        print("[INFO] Abriendo SIMIT...")
        page.goto("https://www.fcm.org.co/simit/#/home-public", timeout=90000)

        # Cerrar modal si aparece
        try:
            page.wait_for_selector('button.modal-info-close', timeout=5000)
            page.click('button.modal-info-close')
            print("[INFO] Modal cerrado.")
        except TimeoutError:
            print("[INFO] No apareció modal informativo.")

        # Ingresar placa y buscar
        page.wait_for_selector('#txtBusqueda', timeout=20000)
        page.fill('#txtBusqueda', placa)
        page.click('#consultar')
        print(f"[INFO] Consultando placa: {placa}")
        time.sleep(1)  # Pequeña pausa para que inicie la navegación

        # Esperar redirección y carga
        try:
            page.wait_for_url(f"**/estado-cuenta?numDocPlacaProp={placa}", timeout=60000)
            page.wait_for_selector('#enviarCorreo', timeout=60000)
            print("[INFO] Página de estado de cuenta cargada.")
        except TimeoutError:
            browser.close()
            raise Exception(f"No se cargó el estado de cuenta para la placa {placa}.")

        # Abrir modal para descargar el PDF
        page.click('[data-target="#modal-estado-cuenta"]')
        print("[INFO] Clic en 'Guardar estado'.")
        page.wait_for_selector('a.btn.btn-outline-primary.btn-block.btn-sm', timeout=30000)

        # Descargar el archivo
        with page.expect_download(timeout=60000) as download_info:
            page.click('a.btn.btn-outline-primary.btn-block.btn-sm')
        download = download_info.value

        os.makedirs(folder, exist_ok=True)
        pdf_path = os.path.join(folder, f'simit_{placa}.pdf')
        download.save_as(pdf_path)

        print(f"[INFO] PDF descargado en: {pdf_path}")
        browser.close()
        return pdf_path
