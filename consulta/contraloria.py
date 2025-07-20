import os
import time
import requests
from playwright.sync_api import sync_playwright

CAPSOLVER_API_KEY = "CAP-99C7B12571DFBDC693C4EFACEE4D9F64BD7678F38556667407E34ABBEEA59830"
SITE_KEY = "6LcfnjwUAAAAAIyl8ehhox7ZYqLQSVl_w1dmYIle"
PAGE_URL = "https://cfiscal.contraloria.gov.co/certificados/certificadopersonanatural.aspx"

def resolver_captcha_capsolver():
    response = requests.post(
        "https://api.capsolver.com/createTask",
        json={
            "clientKey": CAPSOLVER_API_KEY,
            "task": {
                "type": "ReCaptchaV2TaskProxyLess",
                "websiteURL": PAGE_URL,
                "websiteKey": SITE_KEY
            }
        }
    ).json()

    if response.get("errorId") != 0:
        raise Exception(f"Error creando tarea captcha: {response}")

    task_id = response.get("taskId")
    print(f"Tarea captcha creada, taskId: {task_id}")

    for i in range(24):
        time.sleep(5)
        result = requests.post(
            "https://api.capsolver.com/getTaskResult",
            json={
                "clientKey": CAPSOLVER_API_KEY,
                "taskId": task_id
            }
        ).json()

        if result.get("status") == "ready":
            solution = result["solution"]["gRecaptchaResponse"]
            print("Captcha resuelto correctamente.")
            return solution
        elif result.get("status") == "processing":
            print(f"Captcha aún procesándose... ({i+1}/24)")
        else:
            raise Exception(f"Error consultando captcha: {result}")

    raise Exception("Timeout esperando la resolución del captcha con CapSolver")

def consultar_contraloria(cedula, folder):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        page.goto(PAGE_URL)

        page.select_option('#ddlTipoDocumento', 'TI')
        page.fill('#txtNumeroDocumento', cedula)

        token = resolver_captcha_capsolver()

        page.evaluate(f'''
            () => {{
                let recaptchaResponse = document.getElementById('g-recaptcha-response');
                if (!recaptchaResponse) {{
                    recaptchaResponse = document.createElement('textarea');
                    recaptchaResponse.id = 'g-recaptcha-response';
                    recaptchaResponse.name = 'g-recaptcha-response';
                    recaptchaResponse.style.display = 'none';
                    document.body.appendChild(recaptchaResponse);
                }}
                recaptchaResponse.value = "{token}";
            }}
        ''')

        page.wait_for_timeout(1000)

        with page.expect_download() as download_info:
            page.click('#btnBuscar')

        download = download_info.value

        os.makedirs(folder, exist_ok=True)
        pdf_path = os.path.join(folder, f'contraloria_{cedula}.pdf')
        download.save_as(pdf_path)

        print(f"PDF descargado en: {pdf_path}")

        browser.close()

        return pdf_path
