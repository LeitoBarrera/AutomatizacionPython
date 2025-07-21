import os
from playwright.sync_api import sync_playwright

PAGE_URL = "https://antecedentes.personeriabogota.gov.co/expedicion-antecedentes"

def consultar_personeria(cedula, fecha_expedicion, folder):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Cambia a True si no quieres ver el navegador
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        print("[INFO] Ingresando a la página de Personería...")
        page.goto(PAGE_URL, timeout=60000)

        # Seleccionar tipo de documento: '1' = Cédula de Ciudadanía
        page.select_option('#tipo_documento', '1')
        print("[INFO] Tipo de documento seleccionado.")

        # Ingresar número de documento
        page.fill('#documento', cedula)
        print(f"[INFO] Documento {cedula} ingresado.")

        # Eliminar readonly para poder manipular el campo de fecha
        page.evaluate("document.getElementById('fecha_expedicion').removeAttribute('readonly')")

        # Usar Flatpickr para setear la fecha correctamente y disparar eventos
        page.evaluate(f"""
            var fp = document.getElementById('fecha_expedicion')._flatpickr;
            if(fp) {{
                fp.setDate('{fecha_expedicion}', true);
            }}
        """)
        print(f"[INFO] Fecha de expedición {fecha_expedicion} ingresada correctamente con Flatpickr.")

        # Enviar formulario
        page.click('button[type="submit"]')
        print("[INFO] Formulario enviado, esperando resultados...")

        # Esperar que aparezca el botón para descargar certificado
        page.wait_for_selector('.btn.btn-link.my-2.ms-1', timeout=30000)
        print("[INFO] Botón de descarga disponible, iniciando descarga...")

        # Descargar el PDF al folder indicado
        with page.expect_download() as download_info:
            page.click('.btn.btn-link.my-2.ms-1')

        download = download_info.value
        os.makedirs(folder, exist_ok=True)
        pdf_path = os.path.join(folder, f'personeria_{cedula}.pdf')
        download.save_as(pdf_path)

        print(f"[INFO] PDF descargado en: {pdf_path}")

        browser.close()
        return pdf_path
