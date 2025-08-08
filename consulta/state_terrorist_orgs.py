# consulta/state_terrorist_orgs.py
import os, time, urllib.parse, random
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
}

def _anti_automation(page):
    # Suaviza señales de automatización (ya viene algo con Playwright, esto añade)
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    """)

def _aceptar_cookies(page):
    # Acepta Complianz u OneTrust si aparecen
    for sel in [
        "button.cmplz-btn.cmplz-accept",
        "div.cmplz-buttons >> button:has-text('Accept')",
        "#onetrust-accept-btn-handler",
        "button:has-text('Accept')"
    ]:
        try:
            page.locator(sel).first.click(timeout=2000)
            return True
        except Exception:
            pass
    return False

def _es_403(page):
    try:
        txt = page.inner_text("body", timeout=2000)
        return "403 ERROR" in txt and "cloudfront" in txt.lower()
    except Exception:
        return False

def _fallback_search(page, nombre, out_path):
    q = urllib.parse.quote_plus(nombre)
    # Variantes del buscador oficial (DigitalGov)
    candidates = [
        f"https://search.state.gov/?q={q}&affiliate=state.gov&_={random.randint(1,10**9)}",
        f"https://search.state.gov/search?utf8=%E2%9C%93&affiliate=state.gov&query={q}&_={random.randint(1,10**9)}",
    ]
    for u in candidates:
        try:
            page.goto(u, timeout=120000, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle", timeout=15000)
            page.screenshot(path=out_path, full_page=True)
            print(f"[STATE] Fallback OK. Captura: {out_path}")
            return
        except Exception:
            continue
    # Si todo falla, al menos guarda lo que haya
    page.screenshot(path=out_path, full_page=True)
    print(f"[STATE] Fallback agotado. Captura: {out_path}")

def _intentarlo(browser_type, url, nombre, out_path):
    # browser_type: "chromium" o "firefox"
    with sync_playwright() as p:
        browser = getattr(p, browser_type).launch(headless=False,
            args=["--disable-blink-features=AutomationControlled"] if browser_type=="chromium" else None
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

        print(f"[STATE] ({browser_type}) Abriendo {url} …")
        page.goto(url, timeout=120000, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        _aceptar_cookies(page)
        time.sleep(0.8)

        if _es_403(page):
            print(f"[STATE] ({browser_type}) 403 detectado tras cargar.")
            browser.close()
            return False  # señal de 403

        # Intentar flujo normal: abrir lupa, escribir, Enter
        try:
            page.locator("button.nav__search-trigger").click(timeout=8000)
        except Exception:
            # intenta de nuevo tras un pequeño delay
            page.wait_for_timeout(1000)
            page.locator("button.nav__search-trigger").click(timeout=8000)

        page.fill("#nav__search-query", nombre)
        page.keyboard.press("Enter")
        print(f"[STATE] ({browser_type}) Enviando búsqueda…")

        # Normalmente redirige a search.state.gov
        try:
            page.wait_for_url("**search.state.gov**", timeout=20000)
        except Exception:
            pass

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            page.wait_for_timeout(3000)

        if _es_403(page):
            print(f"[STATE] ({browser_type}) 403 en resultados.")
            browser.close()
            return False

        page.screenshot(path=out_path, full_page=True)
        print(f"[STATE] ({browser_type}) Captura guardada: {out_path}")
        browser.close()
        return True

def consultar_state_terrorist_orgs(nombre, folder):
    """
    1) Intenta flujo normal en Chromium; si hay 403 -> prueba Firefox.
    2) Si sigue habiendo 403, usa directamente search.state.gov (fallback).
    """
    os.makedirs(folder, exist_ok=True)
    safe = (nombre or "consulta").strip()
    out_path = os.path.join(folder, f"state_{safe.replace(' ', '_')}.png")

    url = "https://www.state.gov/foreign-terrorist-organizations/"

    # 1) Chromium
    ok = _intentarlo("chromium", url, nombre, out_path)
    if ok:
        return out_path

    # 2) Firefox
    ok = _intentarlo("firefox", url, nombre, out_path)
    if ok:
        return out_path

    # 3) Fallback directo al buscador
    print("[STATE] Usando fallback directo…")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent=UA,
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers=HEADERS,
        )
        page = context.new_page()
        _fallback_search(page, nombre, out_path)
        browser.close()
    return out_path
