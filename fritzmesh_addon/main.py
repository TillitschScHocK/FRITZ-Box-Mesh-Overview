#!/usr/bin/env python3
"""
Fritz!Box Mesh Overview - Selenium-basierte Screenshot-Anwendung
Kompatibel mit FritzOS 8.0+ (Javascript-obfuskiert)
"""

import os
import sys
import time
import logging
import threading
from pathlib import Path
from flask import Flask, send_file, render_template_string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    NoSuchElementException,
)

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

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__)
app.logger.setLevel(logging.ERROR)

# Globale Variablen
driver = None
driver_lock = threading.Lock()
last_screenshot_time = 0


# ============== CHROME DRIVER FUNCTIONS ==============
def get_chrome_options():
    """Erstellt Chrome-Optionen für Headless-Betrieb"""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    return options


def create_driver():
    """Erstellt einen neuen Chrome WebDriver"""
    global driver
    try:
        logger.info("Erstelle Chrome WebDriver...")
        options = get_chrome_options()
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(45)
        driver.set_script_timeout(30)
        
        # Anti-Detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logger.info("✓ Chrome WebDriver bereit")
        return driver
    except Exception as e:
        logger.error(f"✗ Fehler beim Erstellen des Drivers: {e}")
        if driver:
            try:
                driver.quit()
            except:
                pass
            driver = None
        raise


def close_driver():
    """Schließt den WebDriver"""
    global driver
    if driver:
        try:
            driver.quit()
            logger.info("Chrome WebDriver geschlossen")
        except:
            pass
        driver = None


# ============== LOGIN FUNCTION ==============
def perform_login():
    """Führt Login in FritzBox durch"""
    global driver
    try:
        logger.info(f"Navigiere zu {FRITZ_URL}...")
        driver.get(FRITZ_URL)
        time.sleep(2)

        # Prüfe ob Login nötig ist
        try:
            logger.info("Suche Login-Formular...")
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "uiPassInput"))
            )
            logger.info("Login-Formular gefunden")
        except TimeoutException:
            logger.info("Kein Login nötig - bereits eingeloggt")
            return True

        # Benutzer auswählen (falls mehrere)
        try:
            user_select = driver.find_element(By.ID, "uiViewUser")
            user_options = user_select.find_elements(By.TAG_NAME, "option")
            selected_user = None
            for option in user_options:
                if option.get_attribute("value") == FRITZ_USER:
                    selected_user = option
                    break
            if selected_user:
                selected_user.click()
                logger.info(f"Benutzer '{FRITZ_USER}' ausgewählt")
                time.sleep(0.5)
        except NoSuchElementException:
            logger.info("Benutzer-Dropdown nicht vorhanden")

        # Passwort eingeben
        logger.info("Gebe Passwort ein...")
        password_field = driver.find_element(By.ID, "uiPassInput")
        password_field.clear()
        time.sleep(0.2)
        password_field.send_keys(FRITZ_PASS)
        time.sleep(0.5)
        password_field.send_keys(Keys.RETURN)
        logger.info("Login-Anfrage gesendet")

        # Warte auf erfolgreichen Login
        time.sleep(4)

        # Prüfe ob Login erfolgreich
        if "login" not in driver.current_url.lower():
            logger.info("✓ Login erfolgreich!")
            return True
        else:
            logger.error("✗ Login fehlgeschlagen")
            return False

    except Exception as e:
        logger.error(f"Login-Fehler: {e}")
        return False


# ============== MESH NAVIGATION ==============
def navigate_to_mesh():
    """Navigiert zur Mesh-Übersicht"""
    global driver
    try:
        mesh_url = f"{FRITZ_URL}/#/mesh"
        logger.info(f"Navigiere zu Mesh: {mesh_url}")
        driver.get(mesh_url)
        time.sleep(3)

        # Warte auf js3-view Element
        logger.info("Warte auf Mesh-Rendering...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "js3-view"))
        )
        logger.info("✓ Mesh-Seite geladen")

        # Warte noch etwas für vollständiges Rendering
        time.sleep(3)
        return True

    except TimeoutException:
        logger.warning("Mesh-Element nicht gefunden, versuche trotzdem Screenshot...")
        return True
    except Exception as e:
        logger.error(f"Mesh-Navigation Fehler: {e}")
        return False


# ============== SCREENSHOT FUNCTION ==============
def take_screenshot():
    """Macht einen Screenshot der Mesh-Übersicht"""
    global driver, last_screenshot_time
    try:
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
        driver.save_screenshot(SCREENSHOT_PATH)
        last_screenshot_time = time.time()
        return True
    except Exception as e:
        logger.error(f"Screenshot-Fehler: {e}")
        return False


# ============== MAIN BROWSER LOOP ==============
def browser_loop():
    """Haupt-Loop: Authentifizierung und Screenshot-Erfassung"""
    global driver
    error_count = 0
    max_errors = 3

    while True:
        try:
            # Driver erstellen
            if driver is None:
                create_driver()
                error_count = 0

            # Login durchführen
            if not perform_login():
                raise Exception("Login failed")

            # Zur Mesh-Seite navigieren
            if not navigate_to_mesh():
                raise Exception("Mesh navigation failed")

            logger.info("=" * 50)
            logger.info(f"✓ Bereit! Screenshots alle {REFRESH_RATE}s")
            logger.info("=" * 50)

            # Screenshot-Loop
            screenshot_count = 0
            session_start = time.time()

            while True:
                # Session nach 30 Minuten neu laden
                if time.time() - session_start > 1800:
                    logger.info("Session-Refresh nach 30 Minuten")
                    break

                # Screenshot machen
                if take_screenshot():
                    screenshot_count += 1
                    if screenshot_count % 10 == 1:
                        logger.info(f"Screenshot #{screenshot_count} erfasst")
                    error_count = 0
                else:
                    error_count += 1
                    if error_count >= max_errors:
                        logger.error("Zu viele Screenshot-Fehler")
                        break

                # Warten bis nächster Screenshot
                time.sleep(REFRESH_RATE)

        except WebDriverException as e:
            logger.warning(f"WebDriver-Fehler: {e}")
            error_count += 1
        except Exception as e:
            logger.warning(f"Fehler: {e}")
            error_count += 1
        finally:
            # Cleanup
            close_driver()

        # Wartezeit vor Neustart
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
            }}
            .container {{
                background: white;
                border-radius: 10px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 20px;
                max-width: 90vw;
                max-height: 90vh;
                display: flex;
                flex-direction: column;
            }}
            h1 {{
                color: #333;
                margin-bottom: 10px;
                font-size: 24px;
            }}
            .info {{
                color: #666;
                font-size: 12px;
                margin-bottom: 15px;
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
            .loading {{
                text-align: center;
                color: #999;
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
            <h1>🌐 Fritz!Box Mesh</h1>
            <div class="info">Auto-Refresh: {REFRESH_RATE}s</div>
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
    logger.info("Fritz!Box Mesh Overview v2.0.2")
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
        close_driver()
        sys.exit(0)
