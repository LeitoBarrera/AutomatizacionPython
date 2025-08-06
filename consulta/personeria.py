import os
from playwright.sync_api import sync_playwright

PAGE_URL = "https://antecedentes.personeriabogota.gov.co/expedicion-antecedentes"

def consultar_personeria(cedula, fecha_expedicion, folder):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        print("[INFO] Ingresando a la página de Personería...")
        page.goto(PAGE_URL, timeout=120000)  # Más tiempo de carga

        page.select_option('#tipo_documento', '1')
        page.fill('#documento', cedula)

        # Forzar que el campo fecha acepte escritura
        page.evaluate("document.getElementById('fecha_expedicion').removeAttribute('readonly')")
        page.evaluate(f"""
            var fp = document.getElementById('fecha_expedicion')._flatpickr;
            if(fp) fp.setDate('{fecha_expedicion}', true);
        """)

        print(f"[INFO] Fecha {fecha_expedicion} ingresada correctamente.")

        # Esperar botón submit y enviar
        page.click('button[type="submit"]')
        print("[INFO] Formulario enviado, esperando botón de descarga...")

        # Esperar que aparezca el botón de descarga
        page.wait_for_selector('.btn.btn-link.my-2.ms-1', timeout=60000)

        # Descargar PDF de forma segura
        os.makedirs(folder, exist_ok=True)
        pdf_path = os.path.join(folder, f'personeria_{cedula}.pdf')

        with page.expect_download(timeout=120000) as download_info:
            page.click('.btn.btn-link.my-2.ms-1')
        download = download_info.value
        download.save_as(pdf_path)

        print(f"[INFO] PDF descargado en: {pdf_path}")
        browser.close()
        return pdf_path
