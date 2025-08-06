# import os
# import time
# import requests
# from playwright.sync_api import sync_playwright

# CAPSOLVER_API_KEY = "CAP-99C7B12571DFBDC693C4EFACEE4D9F64BD7678F38556667407E34ABBEEA59830"
# PAGE_URL = "https://antecedentes.policia.gov.co:7005/WebJudicial/antecedentes.xhtml"  # Portal real

# # Clave del reCAPTCHA en la página (puede cambiar)
# SITE_KEY = "6Le-wG0UAAAAAH2zv1fO9YB8uhy-5R2z3lFkxJ2C"  

# def resolver_captcha_capsolver():
#     resp = requests.post(
#         "https://api.capsolver.com/createTask",
#         json={
#             "clientKey": CAPSOLVER_API_KEY,
#             "task": {
#                 "type": "ReCaptchaV2TaskProxyLess",
#                 "websiteURL": PAGE_URL,
#                 "websiteKey": SITE_KEY
#             }
#         }
#     ).json()

#     if resp.get("errorId") != 0:
#         raise Exception(f"Error creando tarea captcha: {resp}")

#     task_id = resp.get("taskId")
#     print(f"[INFO] Tarea captcha creada, taskId: {task_id}")

#     for i in range(24):  # máx ~2 min
#         time.sleep(5)
#         result = requests.post(
#             "https://api.capsolver.com/getTaskResult",
#             json={
#                 "clientKey": CAPSOLVER_API_KEY,
#                 "taskId": task_id
#             }
#         ).json()

#         if result.get("status") == "ready":
#             solution = result["solution"]["gRecaptchaResponse"]
#             print("[INFO] Captcha resuelto correctamente.")
#             return solution
#         elif result.get("status") == "processing":
#             print(f"[INFO] Captcha procesándose... ({i+1}/24)")
#         else:
#             raise Exception(f"Error consultando captcha: {result}")

#     raise Exception("Timeout esperando la resolución del captcha")


# def consultar_policia_nacional(cedula, folder, tipo_doc="1"):
#     """
#     tipo_doc: '1' para Cédula de Ciudadanía, '2' para Cédula de Extranjería, etc.
#     """
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         context = browser.new_context(accept_downloads=True)
#         page = context.new_page()

#         print("[INFO] Ingresando a la página de la Policía...")
#         page.goto(PAGE_URL, timeout=60000)

#         # Seleccionar tipo de documento y llenar número
#         page.select_option('select[name="frmConsulta:tipoDoc"]', tipo_doc)
#         page.fill('input[name="frmConsulta:numDoc"]', cedula)
#         print(f"[INFO] Documento {cedula} ingresado con tipo {tipo_doc}.")

#         # Resolver captcha
#         token = resolver_captcha_capsolver()

#         # Inyectar token en el DOM
#         page.evaluate(
#             """token => {
#                 let recaptchaResponse = document.getElementById('g-recaptcha-response');
#                 if (!recaptchaResponse) {
#                     recaptchaResponse = document.createElement('textarea');
#                     recaptchaResponse.id = 'g-recaptcha-response';
#                     recaptchaResponse.name = 'g-recaptcha-response';
#                     recaptchaResponse.style.display = 'none';
#                     document.body.appendChild(recaptchaResponse);
#                 }
#                 recaptchaResponse.value = token;
#             }""",
#             token
#         )

#         page.wait_for_timeout(1500)

#         # Simular clic en el botón consultar
#         with page.expect_download(timeout=90000) as download_info:
#             page.click('input[name="frmConsulta:btnConsultar"]')

#         # Guardar PDF
#         download = download_info.value
#         os.makedirs(folder, exist_ok=True)
#         pdf_path = os.path.join(folder, f'policia_{cedula}.pdf')
#         download.save_as(pdf_path)

#         print(f"[INFO] PDF descargado en: {pdf_path}")

#         browser.close()
#         return pdf_path


# # Ejemplo de uso
# if __name__ == "__main__":
#     try:
#         ruta = consultar_policia("123456789", "output_policia")
#         print(f"[OK] Archivo descargado en: {ruta}")
#     except Exception as e:
#         print(f"[ERROR] {e}")
