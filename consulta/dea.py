from playwright.sync_api import sync_playwright
import os
import time

def consultar_dea(cedula, carpeta_descargas):
    url = "https://www.dea.gov/es/node/11286"
    os.makedirs(carpeta_descargas, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(3000)

        # 1️⃣ Llenar campo de búsqueda
        page.fill("#edit-keywords", cedula)
        page.wait_for_timeout(1000)

        # 2️⃣ Click en botón buscar
        page.click(".menu--search-box-button")
        page.wait_for_timeout(5000)

        # 3️⃣ Intentar detectar resultados
        resultados = page.locator("div.view-content")
        tiene_resultados = resultados.count() > 0

        # 4️⃣ Generar PDF de la página
        pdf_path = os.path.join(carpeta_descargas, f"dea_{cedula}_{int(time.time())}.pdf")
        page.pdf(path=pdf_path, format="A4")
        
        browser.close()
        return pdf_path
