from playwright.sync_api import sync_playwright
import time
import os

def consultar_rama_judicial(nombre_o_razon, tipo_persona, carpeta_descargas):
    url = "https://consultaprocesos.ramajudicial.gov.co/Procesos/NombreRazonSocial"
    os.makedirs(carpeta_descargas, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        page.goto(url, timeout=60000)
        page.wait_for_timeout(3000)

        # 1️⃣ Abrir dropdown de tipo persona
        page.click("#input-72", timeout=10000)
        time.sleep(1)

        # 2️⃣ Seleccionar opción
        if tipo_persona.lower() == "natural":
            page.get_by_text("Natural", exact=True).click()
        else:
            page.get_by_text("Jurídica", exact=True).click()
        time.sleep(1)

        # 3️⃣ Llenar campo de nombre o razón social
        page.fill("#input-78", nombre_o_razon)
        time.sleep(1)

        # 4️⃣ Click en botón Consultar
        page.locator("button[aria-label='Consultar por nombre o razón social']").click()
        page.wait_for_timeout(5000)

        # 5️⃣ Verificar si aparece popup
        popup = page.locator("div.v-dialog.v-dialog--active")
        if popup.is_visible():
            texto_popup = popup.inner_text(timeout=3000)
            print("[INFO] Popup detectado.")

            # Caso: No hay resultados
            if "La consulta no generó resultados" in texto_popup:
                print("[INFO] No se encontraron resultados. Tomando captura...")
                screenshot_path = os.path.join(carpeta_descargas, f"rama_judicial_{int(time.time())}.png")
                page.screenshot(path=screenshot_path, full_page=True)
                page.locator("button:has-text('VOLVER')").click()
                page.wait_for_timeout(2000)
                browser.close()
                return screenshot_path

            # Caso: Hallazgos encontrados
            else:
                print("[INFO] Hallazgos encontrados. Volviendo para descargar DOC...")
                page.locator("button:has-text('VOLVER')").click()
                page.wait_for_timeout(2000)

                # Descargar DOC
                with page.expect_download() as download_info:
                    page.locator("button:has-text('Descargar DOC')").click()
                download = download_info.value

                archivo_doc = os.path.join(carpeta_descargas, f"rama_judicial_{int(time.time())}.doc")
                download.save_as(archivo_doc)
                browser.close()
                return archivo_doc

        # Si no aparece popup
        print("[INFO] No apareció popup. Tomando captura por seguridad.")
        screenshot_path = os.path.join(carpeta_descargas, f"rama_judicial_{int(time.time())}.png")
        page.screenshot(path=screenshot_path, full_page=True)
        browser.close()
        return screenshot_path
