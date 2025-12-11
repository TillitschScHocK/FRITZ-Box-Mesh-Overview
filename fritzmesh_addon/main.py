#!/usr/bin/env python3
"""
Fritz!Box Mesh Overview - Playwright-basierte Anwendung
Kompatibel mit FritzOS 8.0+ (Javascript-obfuskiert)
Schnell und stabil ohne Chrome-Installation
"""

import os
import sys
import time
import logging
import threading
import asyncio
from pathlib import Path
from flask import Flask, send_file, render_template_string
from playwright.async_api import async_playwright

# ============== KONFIGURATION ==============
FRITZ_HOST = os.getenv("FRITZ_HOST", "fritz.box")
FRITZ_PASS = os.getenv("FRITZ_PASS", "")
FRITZ_USER = os.getenv("FRITZ_USER", "Admin")
REFRESH_RATE = int(os.getenv("REFRESH_RATE", "10"))

# URL konstruieren
if not FRITZ_HOST.startswith(("http://", "https://")):
    FRITZ_URL = f"http://{FRITZ_HOST}"
else:
    FRITZ_URL = FRITZ_HOST

# Pfade
SCREENSHOT_PATH = "/app/static/mesh.png"
Path("/app/static").mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__)
app.logger.setLevel(logging.ERROR)

# Globale Variablen
last_screenshot_time = 0


# ============== PLAYWRIGHT FUNCTIONS ==============
async def login_to_fritz(page):
    """Authentifiziert sich bei der FritzBox"""
    try:
        logger.info(f"Öffne {FRITZ_URL}...")
        await page.goto(FRITZ_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)

        # Prüfe ob Login notwendig ist
        try:
            login_field = page.query_selector("#uiPassInput")
            if login_field is None:
                logger.info("Bereits angemeldet")
                return True

            logger.info("Login-Formular gefunden")

            # Benutzer-Dropdown (optional)
            try:
                user_select = page.query_selector("#uiViewUser")
                if user_select:
                    await user_select.select_option(value=FRITZ_USER)
                    logger.info(f"Benutzer '{FRITZ_USER}' ausgewählt")
                    await page.wait_for_timeout(500)
            except:
                pass

            # Passwort eingeben
            logger.info("Gebe Passwort ein...")
            await page.fill("#uiPassInput", FRITZ_PASS)
            await page.wait_for_timeout(300)

            # Login-Button suchen und klicken
            login_btn = page.query_selector("#submitLoginBtn")
            if login_btn:
                await login_btn.click()
                logger.info("Login-Button geklickt")
            else:
                # Fallback: Enter drücken
                await page.press("#uiPassInput", "Enter")
                logger.info("Enter gedrückt")

            # Warte auf Weiterleitung
            await page.wait_for_timeout(4000)

            # Prüfe ob erfolgreich
            current_url = page.url.lower()
            if "login" not in current_url and "anmeldung" not in current_url:
                logger.info("✓ Login erfolgreich!")
                return True
            else:
                logger.error("✗ Login fehlgeschlagen")
                return False

        except Exception as e:
            logger.error(f"Login-Fehler: {e}")
            return False

    except Exception as e:
        logger.error(f"Fehler beim Öffnen der Seite: {e}")
        return False


async def navigate_to_mesh(page):
    """Navigiert zur Mesh-Übersicht"""
    try:
        mesh_url = f"{FRITZ_URL}/#/mesh"
        logger.info(f"Navigiere zu Mesh: {mesh_url}")
        await page.goto(mesh_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)

        # Warte auf js3-view Element
        try:
            await page.wait_for_selector("js3-view", timeout=10000)
            logger.info("✓ Mesh-Seite geladen")
            await page.wait_for_timeout(2000)
            return True
        except:
            logger.warning("js3-view nicht gefunden, versuche trotzdem Screenshot...")
            return True

    except Exception as e:
        logger.error(f"Mesh-Navigation Fehler: {e}")
        return False


async def take_screenshot(page):
    """Macht einen Screenshot"""
    global last_screenshot_time
    try:
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(500)
        await page.screenshot(path=SCREENSHOT_PATH, full_page=False)
        last_screenshot_time = time.time()
        return True
    except Exception as e:
        logger.error(f"Screenshot-Fehler: {e}")
        return False


async def browser_session():
    """Haupt-Browser-Session"""
    async with async_playwright() as p:
        try:
            logger.info("Starte Chromium Browser...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = await context.new_page()

            # User-Agent setzen
            await page.set_user_agent(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )

            # Login
            if not await login_to_fritz(page):
                raise Exception("Login failed")

            # Zur Mesh-Seite navigieren
            if not await navigate_to_mesh(page):
                raise Exception("Mesh navigation failed")

            logger.info("=" * 50)
            logger.info(f"✓ Bereit! Screenshots alle {REFRESH_RATE}s")
            logger.info("=" * 50)

            # Screenshot-Loop
            screenshot_count = 0
            error_count = 0
            session_start = time.time()

            while True:
                # Nach 30 Minuten neu laden
                if time.time() - session_start > 1800:
                    logger.info("Session-Refresh nach 30 Minuten")
                    break

                # Screenshot machen
                if await take_screenshot(page):
                    screenshot_count += 1
                    if screenshot_count % 10 == 1:
                        logger.info(f"Screenshot #{screenshot_count} erfasst")
                    error_count = 0
                else:
                    error_count += 1
                    if error_count >= 5:
                        logger.error("Zu viele Screenshot-Fehler")
                        break

                # Warten bis nächster Screenshot
                await page.wait_for_timeout(REFRESH_RATE * 1000)

            await context.close()
            await browser.close()

        except Exception as e:
            logger.error(f"Browser-Session Fehler: {e}")
        finally:
            try:
                await context.close()
                await browser.close()
            except:
                pass


def browser_loop():
    """Wrapper für Async-Browser-Loop"""
    error_count = 0
    max_errors = 3

    while True:
        try:
            asyncio.run(browser_session())
            error_count = 0
        except Exception as e:
            logger.error(f"Browser-Loop Fehler: {e}")
            error_count += 1
        finally:
            if error_count >= max_errors:
                logger.info("Warte 60s vor Neustart...")
                time.sleep(60)
                error_count = 0
            else:
                logger.info("Warte 10s vor Neustart...")
                time.sleep(10)


# ============== FLASK ROUTES ==============
@app.route("/")
def index():
    """Haupt-Webseite mit Auto-Refresh"""
    html = f"""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Fritz!Box Mesh</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                padding: 10px;
            }}
            .container {{
                background: white;
                border-radius: 10px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 20px;
                max-width: 95vw;
                max-height: 95vh;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }}
            h1 {{
                color: #333;
                font-size: 20px;
                margin: 0;
            }}
            .info {{
                color: #666;
                font-size: 12px;
            }}
            .image-container {{
                flex: 1;
                display: flex;
                justify-content: center;
                align-items: center;
                overflow: auto;
                background: #f5f5f5;
                border-radius: 8px;
                min-height: 400px;
            }}
            img {{
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
            }}
        </style>
        <script>
            function updateImage() {{
                var img = document.getElementById('mesh-img');
                img.src = '/mesh.png?t=' + Date.now();
            }}
            setInterval(updateImage, {REFRESH_RATE * 1000});
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🌐 Fritz!Box Mesh Übersicht</h1>
            <div class="info">Auto-Update: {REFRESH_RATE}s</div>
            <div class="image-container">
                <img id="mesh-img" src="/mesh.png" alt="Lädt...">
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route("/mesh.png")
def get_image():
    """Liefert das Screenshot-Bild"""
    if os.path.exists(SCREENSHOT_PATH):
        return send_file(
            SCREENSHOT_PATH,
            mimetype="image/png",
            max_age=0,
            add_etags=False,
        )
    return "Keine Daten verfügbar", 503


@app.route("/health")
def health():
    """Health-Check"""
    if os.path.exists(SCREENSHOT_PATH):
        age = time.time() - os.path.getmtime(SCREENSHOT_PATH)
        status = "ok" if age < (REFRESH_RATE * 3) else "stale"
        return {"status": status, "age": int(age)}, 200
    return {"status": "no_image"}, 503


# ============== MAIN ==============
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Fritz!Box Mesh Overview v2.1")
    logger.info("=" * 50)
    logger.info(f"Host: {FRITZ_URL}")
    logger.info(f"Benutzer: {FRITZ_USER}")
    logger.info(f"Refresh-Rate: {REFRESH_RATE}s")
    logger.info(f"Passwort: {'✓ Gesetzt' if FRITZ_PASS else '✗ NICHT GESETZT'}")
    logger.info("=" * 50)

    # Browser-Thread starten
    browser_thread = threading.Thread(target=browser_loop, daemon=True)
    browser_thread.start()

    # Flask-Server starten
    logger.info("Starte Webserver auf Port 8000...")
    try:
        app.run(host="0.0.0.0", port=8000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Herunterfahren...")
        sys.exit(0)
