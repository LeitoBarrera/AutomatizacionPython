import os
import time
from playwright.sync_api import sync_playwright

def consultar_simit(placa, folder):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        print("[INFO] Abriendo SIMIT...")
        page.goto("https://www.fcm.org.co/simit/#/home-public", timeout=60000)

        # Cerrar modal si aparece
        try:
            page.wait_for_selector('button.modal-info-close', timeout=5000)
            page.click('button.modal-info-close')
            print("[INFO] Modal cerrado.")
        except:
            print("[INFO] No apareció modal informativo.")

        # Ingresar placa y buscar
        page.wait_for_selector('#txtBusqueda', timeout=15000)
        page.fill('#txtBusqueda', placa)
        page.click('#consultar')
        print(f"[INFO] Consultando placa: {placa}")

        # Esperar redirección y carga
        page.wait_for_url(f"**/estado-cuenta?numDocPlacaProp={placa}", timeout=30000)
        page.wait_for_selector('#enviarCorreo', timeout=60000)
        print("[INFO] Página de estado de cuenta cargada.")

        # Clic en "Guardar estado" para abrir el modal del PDF
        page.click('[data-target="#modal-estado-cuenta"]')
        print("[INFO] Clic en 'Guardar estado'.")

        # Esperar botón de descarga dentro del modal
        page.wait_for_selector('a.btn.btn-outline-primary.btn-block.btn-sm', timeout=30000)

        # Descargar el archivo
        with page.expect_download() as download_info:
            page.click('a.btn.btn-outline-primary.btn-block.btn-sm')
        download = download_info.value

        os.makedirs(folder, exist_ok=True)
        pdf_path = os.path.join(folder, f'simit_{placa}.pdf')
        download.save_as(pdf_path)

        print(f"[INFO] PDF descargado en: {pdf_path}")
        browser.close()
        return pdf_path
