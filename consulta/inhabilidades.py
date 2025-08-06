import time
import requests
from playwright.sync_api import sync_playwright

CAPSOLVER_API_KEY = "CAP-99C7B12571DFBDC693C4EFACEE4D9F64BD7678F38556667407E34ABBEEA59830"
PAGE_URL = "https://inhabilidades.policia.gov.co:8080/"
SITE_KEY = "6LflZLwUAAAAAP6-I_SuqVa1YDSTqfMyk43peb_M"

def resolver_captcha_capsolver():
    print("[INFO] Creando tarea para resolver reCAPTCHA...")
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
    print(f"[INFO] Tarea captcha creada, taskId: {task_id}")

    for i in range(24):  # Máx 2 min
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
            print("[INFO] Captcha resuelto correctamente.")
            return solution
        elif result.get("status") == "processing":
            print(f"[INFO] Captcha procesándose... ({i+1}/24)")

    raise Exception("Timeout esperando la resolución del captcha")


def consultar_inhabilidades(tipo_doc, numero_doc, fecha_exp, empresa, nit, folder="./resultados"):
    print("[INFO] Ingresando a la página de Inhabilidades de la Policía...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        page = browser.new_page()
        page.goto(PAGE_URL, timeout=90000)

        # 1️⃣ Llenar datos básicos
        page.select_option("#tipo", tipo_doc)
        page.fill("#nuip", numero_doc)
        page.fill("#fechaExpNuip", fecha_exp)

        # Primer Tab para cerrar calendario
        page.keyboard.press("Tab")
        page.evaluate("document.querySelector('#fechaExpNuip').blur()")
        time.sleep(0.5)

        # 2️⃣ Llenar datos de empresa
        page.fill("#nombreEmpresa", empresa)
        page.fill("#nitEmpresa", nit)
        time.sleep(1)

        # 3️⃣ Hacer en total 6 Tabs (contando el primero)
        for _ in range(5):  # Ya hicimos 1
            page.keyboard.press("Tab")
            time.sleep(0.2)

        # 4️⃣ Simular click real en el checkbox
        checkbox = page.query_selector("#cbCondiciones")
        if checkbox:
            box = checkbox.bounding_box()
            if box:
                page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                print("[INFO] Checkbox marcado con click real.")
        time.sleep(1)

        # 5️⃣ Resolver Captcha
        print("[INFO] Resolviendo reCAPTCHA...")
        token = resolver_captcha_capsolver()

        # Inyectar token y disparar eventos
        page.evaluate("""
        token => {
            const el = document.getElementById("g-recaptcha-response");
            el.value = token;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        }
        """, token)

        # ✅ Apenas se resuelva el captcha, hacer click en btnConsultar
        page.click("#btnConsultar")
        print("[INFO] Formulario enviado.")

        # 6️⃣ Esperar a que cargue la nueva página (redirección)
        page.wait_for_load_state("networkidle", timeout=60000)
        time.sleep(3)  # Breve espera extra para que cargue todo

        # 7️⃣ Captura de pantalla de la página de resultados
        screenshot_path = f"{folder}/resultado_{numero_doc}.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"[INFO] Captura de resultados guardada en: {screenshot_path}")

        # Mantener abierto 10s para depuración
        page.wait_for_timeout(10000)
        browser.close()
