import os
import time
import threading
import logging
from flask import Flask, send_file, render_template_string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Konfiguration
FRITZ_USER = os.getenv("FRITZ_USER", "")
FRITZ_PASS = os.getenv("FRITZ_PASS", "")
FRITZ_HOST = os.getenv("FRITZ_HOST", "fritz.box")
REFRESH_RATE = int(os.getenv("REFRESH_RATE", "10"))

# FRITZ_HOST bereinigen
if not FRITZ_HOST.startswith(('http://', 'https://')):
    FRITZ_URL = f"http://{FRITZ_HOST}"
else:
    FRITZ_URL = FRITZ_HOST

# Pfade
SCREENSHOT_PATH = "/app/static/mesh.png"
os.makedirs("/app/static", exist_ok=True)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask Logger reduzieren
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

def get_driver():
    """Erstellt einen konfigurierten Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Realistischer User-Agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Sprache setzen
    chrome_options.add_argument("--lang=de-DE")
    
    # Speicher-Optimierungen
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-software-rasterizer")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        
        # WebDriver Property überschreiben (Anti-Detection)
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Drivers: {e}")
        raise

def perform_login(driver):
    """Führt den Login in die FritzBox durch"""
    try:
        # Warte auf Passwortfeld
        logger.info("Warte auf Login-Formular...")
        pass_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "uiPass"))
        )
        
        logger.info("Login-Formular gefunden, gebe Passwort ein...")
        pass_input.clear()
        time.sleep(0.5)
        pass_input.send_keys(FRITZ_PASS)
        time.sleep(0.5)
        
        # Login-Button suchen und klicken
        try:
            login_button = driver.find_element(By.ID, "submitLoginBtn")
            login_button.click()
            logger.info("Login-Button geklickt")
        except:
            # Fallback: Enter-Taste
            pass_input.send_keys(Keys.RETURN)
            logger.info("Enter gedrückt zum Login")
        
        # Warte kurz auf Weiterleitung
        time.sleep(3)
        
        # Prüfe ob Login erfolgreich
        if "login" not in driver.current_url.lower():
            logger.info("Login erfolgreich!")
            return True
        else:
            logger.warning("Login scheint fehlgeschlagen zu sein")
            return False
            
    except TimeoutException:
        logger.info("Kein Login-Formular gefunden, eventuell bereits eingeloggt")
        return True
    except Exception as e:
        logger.error(f"Login-Fehler: {e}")
        return False

def navigate_to_mesh(driver):
    """Navigiert zur Mesh-Übersicht"""
    mesh_urls = [
        f"{FRITZ_URL}/#/homeNet/mesh",
        f"{FRITZ_URL}/#homenet/mesh",
        f"{FRITZ_URL}/#net/mesh",
        f"{FRITZ_URL}/home/home.lua#mesh"
    ]
    
    for mesh_url in mesh_urls:
        try:
            logger.info(f"Versuche Mesh-URL: {mesh_url}")
            driver.get(mesh_url)
            time.sleep(5)
            
            # Prüfe ob Mesh-Übersicht geladen wurde
            # Suche nach typischen Mesh-Elementen
            try:
                # Warte auf ein Element, das auf der Mesh-Seite vorhanden ist
                WebDriverWait(driver, 5).until(
                    lambda d: "mesh" in d.page_source.lower() or 
                             "heimnetz" in d.page_source.lower()
                )
                logger.info(f"Mesh-Seite erfolgreich geladen: {mesh_url}")
                return True
            except:
                continue
                
        except Exception as e:
            logger.warning(f"Fehler bei Mesh-URL {mesh_url}: {e}")
            continue
    
    logger.error("Konnte Mesh-Seite nicht laden")
    return False

def take_screenshot(driver):
    """Erstellt einen Screenshot der aktuellen Seite"""
    try:
        # Scrolle zum Anfang der Seite
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
        
        # Screenshot machen
        driver.save_screenshot(SCREENSHOT_PATH)
        logger.debug("Screenshot erfolgreich erstellt")
        return True
    except Exception as e:
        logger.error(f"Screenshot-Fehler: {e}")
        return False

def browser_loop():
    """Haupt-Loop für Browser-Automation"""
    driver = None
    consecutive_errors = 0
    max_errors = 5
    
    while True:
        try:
            # Driver erstellen wenn nötig
            if driver is None:
                logger.info("Erstelle neuen Chrome-Driver...")
                driver = get_driver()
                consecutive_errors = 0
            
            # Zur FritzBox navigieren
            logger.info(f"Öffne FritzBox: {FRITZ_URL}")
            driver.get(FRITZ_URL)
            time.sleep(3)
            
            # Login durchführen
            if not perform_login(driver):
                logger.error("Login fehlgeschlagen!")
                raise Exception("Login failed")
            
            # Zur Mesh-Seite navigieren
            if not navigate_to_mesh(driver):
                logger.error("Mesh-Navigation fehlgeschlagen!")
                raise Exception("Mesh navigation failed")
            
            # Screenshot-Loop
            logger.info(f"Starte Screenshot-Loop (alle {REFRESH_RATE}s)")
            screenshot_count = 0
            session_start = time.time()
            
            while True:
                # Session-Refresh alle 30 Minuten
                if time.time() - session_start > 1800:
                    logger.info("Session-Refresh nach 30 Minuten")
                    break
                
                # Prüfe ob Session noch gültig
                if "login" in driver.current_url.lower():
                    logger.warning("Session abgelaufen, starte neu...")
                    break
                
                # Screenshot erstellen
                if take_screenshot(driver):
                    screenshot_count += 1
                    if screenshot_count % 10 == 0:
                        logger.info(f"{screenshot_count} Screenshots erstellt")
                    consecutive_errors = 0
                else:
                    consecutive_errors += 1
                    if consecutive_errors >= max_errors:
                        logger.error("Zu viele Screenshot-Fehler, starte Browser neu")
                        break
                
                # Warte bis zum nächsten Screenshot
                time.sleep(REFRESH_RATE)
                
        except WebDriverException as e:
            logger.error(f"WebDriver-Fehler: {e}")
            consecutive_errors += 1
        except Exception as e:
            logger.error(f"Unerwarteter Fehler: {e}")
            consecutive_errors += 1
        
        # Cleanup
        if driver:
            try:
                driver.quit()
                logger.info("Browser geschlossen")
            except:
                pass
            driver = None
        
        # Bei zu vielen Fehlern länger warten
        if consecutive_errors >= max_errors:
            logger.error(f"Zu viele Fehler ({consecutive_errors}), warte 60s...")
            time.sleep(60)
            consecutive_errors = 0
        else:
            logger.info("Warte 10s vor Neustart...")
            time.sleep(10)

# Web-Server Routen
@app.route('/')
def index():
    """Hauptseite mit Auto-Refresh"""
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
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                display: flex; 
                flex-direction: column;
                justify-content: center; 
                align-items: center; 
                min-height: 100vh;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}
            .container {{
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                padding: 20px;
                max-width: 95vw;
                max-height: 95vh;
                overflow: hidden;
            }}
            h1 {{
                color: #1e3c72;
                text-align: center;
                margin-bottom: 15px;
                font-size: 1.8em;
            }}
            .status {{
                text-align: center;
                color: #666;
                font-size: 0.9em;
                margin-bottom: 10px;
            }}
            .image-wrapper {{
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 500px;
            }}
            img {{ 
                max-width: 100%; 
                max-height: 70vh;
                border-radius: 10px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }}
            .loading {{
                color: #666;
                font-style: italic;
            }}
            .last-update {{
                text-align: center;
                color: #888;
                font-size: 0.8em;
                margin-top: 10px;
            }}
        </style>
        <script>
            var refreshRate = {REFRESH_RATE};
            var lastUpdate = new Date();
            
            function updateImage() {{
                var img = document.getElementById('mesh-img');
                var timestamp = new Date().getTime();
                img.src = '/mesh.png?t=' + timestamp;
                lastUpdate = new Date();
                updateTimestamp();
            }}
            
            function updateTimestamp() {{
                var elem = document.getElementById('last-update');
                if (elem) {{
                    elem.textContent = 'Letztes Update: ' + lastUpdate.toLocaleTimeString('de-DE');
                }}
            }}
            
            // Bild alle X Sekunden aktualisieren
            setInterval(updateImage, refreshRate * 1000);
            
            // Timestamp jede Sekunde aktualisieren
            setInterval(updateTimestamp, 1000);
            
            // Fehlerbehandlung für Bild-Ladefehler
            window.addEventListener('load', function() {{
                var img = document.getElementById('mesh-img');
                img.onerror = function() {{
                    console.log('Bild konnte nicht geladen werden, versuche erneut...');
                    setTimeout(updateImage, 2000);
                }};
            }});
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🌐 Fritz!Box Mesh Übersicht</h1>
            <div class="status">
                Automatische Aktualisierung alle {REFRESH_RATE} Sekunden
            </div>
            <div class="image-wrapper">
                <img id="mesh-img" src="/mesh.png" alt="Lade Mesh Übersicht..." 
                     onerror="this.alt='Bild konnte nicht geladen werden. Warte auf nächstes Update...'">
            </div>
            <div class="last-update" id="last-update">Lade...</div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/mesh.png')
def get_image():
    """Liefert das aktuelle Mesh-Screenshot-Bild"""
    if os.path.exists(SCREENSHOT_PATH):
        return send_file(SCREENSHOT_PATH, mimetype='image/png', 
                        max_age=0,  # Kein Caching
                        add_etags=False)
    else:
        return "Noch kein Bild verfügbar. Bitte warten...", 503

@app.route('/health')
def health():
    """Health-Check Endpoint"""
    if os.path.exists(SCREENSHOT_PATH):
        file_age = time.time() - os.path.getmtime(SCREENSHOT_PATH)
        if file_age < (REFRESH_RATE * 3):
            return {"status": "healthy", "screenshot_age": int(file_age)}, 200
        else:
            return {"status": "degraded", "screenshot_age": int(file_age)}, 200
    return {"status": "starting"}, 503

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("Fritz!Box Mesh Overview gestartet")
    logger.info(f"FritzBox URL: {FRITZ_URL}")
    logger.info(f"Refresh Rate: {REFRESH_RATE}s")
    logger.info(f"Passwort gesetzt: {'Ja' if FRITZ_PASS else 'NEIN - BITTE SETZEN!'}")
    logger.info("=" * 50)
    
    # Browser-Thread starten
    thread = threading.Thread(target=browser_loop, daemon=True)
    thread.start()
    
    # Flask-Server starten
    logger.info("Starte Webserver auf Port 8000...")
    app.run(host='0.0.0.0', port=8000, debug=False)
