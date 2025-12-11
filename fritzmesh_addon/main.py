#!/usr/bin/env python3
"""
Fritz!Box Mesh Overview - Playwright-basierte Anwendung
Kompatibel mit FritzOS 8.0+ (Javascript-obfuskiert)
Schnell und stabil
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
async def browser_session():
    """Haupt-Browser-Session mit Mesh-Screenshot"""
    async with async_playwright() as p:
        browser = None
        context = None
        page = None
        
        try:
            logger.info("Starte Chromium Browser...")
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            # Context mit User-Agent erstellen
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()

            # === LOGIN ===
            logger.info(f"Öffne Fritz!Box: {FRITZ_URL}")
            await page.goto(FRITZ_URL, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)

            # Prüfe ob Login nötig ist
            try:
                login_field = await page.query_selector("#uiPassInput")
                
                if login_field:
                    logger.info("Login-Formular gefunden")
                    
                    # Benutzer wählen (falls möglich)
                    try:
                        user_select = await page.query_selector("#uiViewUser")
                        if user_select:
                            await page.select_option("#uiViewUser", value=FRITZ_USER)
                            logger.info(f"Benutzer '{FRITZ_USER}' ausgewählt")
                            await page.wait_for_timeout(300)
                    except Exception as e:
                        logger.debug(f"Benutzer-Auswahl fehlgeschlagen: {e}")
                    
                    # Passwort eingeben
                    logger.info("Gebe Passwort ein...")
                    await page.fill("#uiPassInput", FRITZ_PASS)
                    await page.wait_for_timeout(500)
                    
                    # Login absenden - mit click()
                    logger.info("Klicke Login-Button...")
                    await page.click("#submitLoginBtn")
                    
                    # Warte auf Weiterleitung
                    logger.info("Warte auf Login-Verarbeitung...")
                    await page.wait_for_timeout(5000)
                    logger.info("✓ Login abgeschlossen")
                else:
                    logger.info("Bereits angemeldet (kein Login-Formular)")
            except Exception as e:
                logger.error(f"Login-Fehler: {e}")
                raise

            # === MESH-NAVIGATION ===
            mesh_url = f"{FRITZ_URL}/#/mesh"
            logger.info(f"Navigiere zu Mesh: {mesh_url}")
            await page.goto(mesh_url, wait_until="domcontentloaded", timeout=30000)
            
            logger.info("Warte auf Mesh-Rendering...")
            await page.wait_for_timeout(5000)

            # Warte auf Mesh-Element
            try:
                await page.wait_for_selector("js3-view", timeout=10000)
                logger.info("✓ Mesh-Element geladen")
            except:
                logger.warning("js3-view nicht gefunden, Screenshot trotzdem versuchen")
            
            await page.wait_for_timeout(2000)  # Rendering abwarten

            logger.info("=" * 50)
            logger.info(f"✓ BEREIT! Screenshots alle {REFRESH_RATE}s")
            logger.info("=" * 50)

            # === SCREENSHOT-LOOP ===
            screenshot_count = 0
            error_count = 0
            session_start = time.time()

            while True:
                # Nach 30 Minuten neu laden
                if time.time() - session_start > 1800:
                    logger.info("⟳ Session-Refresh nach 30 Minuten")
                    break

                # Screenshot
                try:
                    await page.evaluate("window.scrollTo(0, 0)")
                    await page.wait_for_timeout(300)
                    await page.screenshot(path=SCREENSHOT_PATH, full_page=False)
                    screenshot_count += 1
                    
                    if screenshot_count == 1:
                        logger.info("✓ Erstes Mesh-Screenshot erfolgreich!")
                    elif screenshot_count % 20 == 0:
                        logger.info(f"✓ Screenshot #{screenshot_count} erfasst")
                    
                    error_count = 0
                except Exception as e:
                    logger.error(f"Screenshot-Fehler: {e}")
                    error_count += 1
                    if error_count >= 5:
                        logger.error("Zu viele Screenshot-Fehler, starte Browser neu")
                        break

                # Warten bis nächster Screenshot
                await page.wait_for_timeout(REFRESH_RATE * 1000)

        except Exception as e:
            logger.error(f"Browser-Fehler: {e}")
        
        finally:
            # Cleanup - Fehler ignorieren
            try:
                if page:
                    await page.close()
                if context:
                    await context.close()
                if browser:
                    await browser.close()
            except:
                pass


def browser_loop():
    """Wrapper für Async-Loop mit Auto-Restart"""
    error_count = 0
    max_errors = 3

    while True:
        try:
            asyncio.run(browser_session())
            error_count = 0
        except Exception as e:
            logger.error(f"Browser-Loop Fehler: {e}")
            error_count += 1
        
        # Warten vor Neustart
        if error_count >= max_errors:
            logger.warning(f"⚠ Zu viele Fehler ({error_count}), warte 60s")
            time.sleep(60)
            error_count = 0
        else:
            logger.info("⟳ Starte Browser neu...")
            time.sleep(5)


# ============== FLASK ROUTES ==============
@app.route("/")
def index():
    """Haupt-Webseite"""
    html = f"""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Fritz!Box Mesh Übersicht</title>
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
                overflow: hidden;
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
            .image-wrapper {{
                flex: 1;
                display: flex;
                justify-content: center;
                align-items: center;
                overflow: auto;
                background: #f9f9f9;
                border-radius: 8px;
                min-height: 400px;
                position: relative;
            }}
            img {{
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
            }}
        </style>
        <script>
            var refreshRate = {REFRESH_RATE};
            
            function updateImage() {{
                var img = document.getElementById('mesh-img');
                var newSrc = '/mesh.png?t=' + Date.now();
                img.src = newSrc;
            }}
            
            window.addEventListener('load', updateImage);
            setInterval(updateImage, refreshRate * 1000);
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🌐 Fritz!Box Mesh Übersicht</h1>
            <div class="info">Automatische Aktualisierung: {REFRESH_RATE} Sekunden</div>
            <div class="image-wrapper">
                <img id="mesh-img" src="/mesh.png" alt="Lädt Mesh-Daten...">
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route("/mesh.png")
def get_image():
    """Liefert das Mesh-Screenshot-Bild"""
    if os.path.exists(SCREENSHOT_PATH):
        return send_file(
            SCREENSHOT_PATH,
            mimetype="image/png",
            max_age=0
        )
    return "Mesh-Daten werden generiert...", 503


@app.route("/health")
def health():
    """Health-Check Endpoint"""
    if os.path.exists(SCREENSHOT_PATH):
        age = time.time() - os.path.getmtime(SCREENSHOT_PATH)
        status = "healthy" if age < (REFRESH_RATE * 3) else "degraded"
        return {"status": status, "age_seconds": int(age)}, 200
    return {"status": "initializing"}, 503


# ============== MAIN ==============
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Fritz!Box Mesh Overview v2.2")
    logger.info("=" * 60)
    logger.info(f"Fritz!Box: {FRITZ_URL}")
    logger.info(f"Benutzer: {FRITZ_USER}")
    logger.info(f"Refresh-Rate: {REFRESH_RATE}s")
    logger.info(f"Passwort: {'✓ Gesetzt' if FRITZ_PASS else '✗ NICHT GESETZT'}")
    logger.info("=" * 60)

    # Browser-Thread starten
    browser_thread = threading.Thread(target=browser_loop, daemon=True)
    browser_thread.start()

    # Flask-Server starten
    logger.info("Starte Webserver auf Port 8000...\n")
    try:
        app.run(
            host="0.0.0.0",
            port=8000,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("Herunterfahren...")
        sys.exit(0)
