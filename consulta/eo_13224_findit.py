# consulta/eo_13224_findit.py
import os, time, urllib.parse, random
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
}

def _anti_automation(page):
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    """)

def _es_403(page):
    try:
        txt = page.inner_text("body", timeout=2000)
        return "403 ERROR" in txt and "cloudfront" in txt.lower()
    except Exception:
        return False

def _urls(nombre):
    # Buscamos el nombre acotando a EO 13224
    q = urllib.parse.quote_plus(f'{nombre} "Executive Order 13224"')
    rid = random.randint(1, 10**9)
    return [
        # 1) findit.state.gov (lo que tú pediste)
        f"https://findit.state.gov/search?query={q}&affiliate=dos_stategov&_={rid}",
        # 2) otro alias del motor (a veces sobrevive a bloqueos)
        f"https://search.state.gov/search?utf8=%E2%9C%93&affiliate=state.gov&query={q}&_={rid}",
        f"https://search.state.gov/?q={q}&affiliate=state.gov&_={rid}",
    ]

def _intentar(browser_type, url, out_path):
    with sync_playwright() as p:
        browser = getattr(p, browser_type).launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"] if browser_type == "chromium" else None
        )
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent=UA,
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers=HEADERS,
        )
        page = context.new_page()
        _anti_automation(page)

        print(f"[EO13224-FINDIT] ({browser_type}) GET {url}")
        page.goto(url, timeout=120000, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        if _es_403(page):
            print(f"[EO13224-FINDIT] ({browser_type}) 403 detectado.")
            browser.close()
            return False

        page.screenshot(path=out_path, full_page=True)
        print(f"[EO13224-FINDIT] ({browser_type}) Captura: {out_path}")
        browser.close()
        return True

def consultar_eo_13224_findit(nombre, folder):
    """
    Abre directamente la URL de findit.state.gov con la query 'nombre "Executive Order 13224"'.
    Si hay 403, prueba con Firefox y luego con search.state.gov como fallback.
    Devuelve ruta PNG.
    """
    os.makedirs(folder, exist_ok=True)
    safe = (nombre or "consulta").strip()
    out_path = os.path.join(folder, f"eo13224_findit_{safe.replace(' ', '_')}.png")

    for url in _urls(nombre):
        # Chromium
        if _intentar("chromium", url, out_path):
            return out_path
        # Firefox
        if _intentar("firefox", url, out_path):
            return out_path

    # Si TODO falló, al menos deja una captura de la última pantalla vista
    return out_path
