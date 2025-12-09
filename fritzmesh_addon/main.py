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
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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
    chrome_options.add_argument("--accept-lang=de-DE,de")
    
    # Speicher-Optimierungen
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-software-rasterizer")
    
    # Performance
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(45)
        driver.set_script_timeout(30)
        
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
        logger.info("Warte auf Login-Formular...")
        
        # Warte auf Passwortfeld - Custom Web Component
        try:
            # Versuche erst das Custom-Input-Element
            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "uiPassInput"))
            )
        except:
            # Fallback auf normales Input
            password_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "uiPass"))
            )
        
        logger.info("Login-Formular gefunden")
        
        # Prüfe ob Benutzer-Dropdown vorhanden ist
        try:
            user_select = driver.find_element(By.ID, "uiViewUser")
            # Wähle Benutzer falls angegeben
            if FRITZ_USER:
                from selenium.webdriver.support.ui import Select
                select = Select(user_select)
                try:
                    select.select_by_value(FRITZ_USER)
                    logger.info(f"Benutzer '{FRITZ_USER}' ausgewählt")
                except:
                    logger.warning(f"Benutzer '{FRITZ_USER}' nicht gefunden, nutze Standard")
            else:
                logger.info("Nutze Standard-Benutzer")
        except NoSuchElementException:
            logger.info("Kein Benutzer-Dropdown vorhanden")
        
        # Passwort eingeben
        logger.info("Gebe Passwort ein...")
        password_input.clear()
        time.sleep(0.3)
        password_input.send_keys(FRITZ_PASS)
        time.sleep(0.5)
        
        # Login-Button klicken
        try:
            login_button = driver.find_element(By.ID, "submitLoginBtn")
            logger.info("Klicke Login-Button...")
            login_button.click()
        except:
            logger.info("Login-Button nicht gefunden, versuche Enter...")
            password_input.send_keys(Keys.RETURN)
        
        # Warte auf erfolgreichen Login
        time.sleep(5)
        
        # Prüfe ob Login erfolgreich
        current_url = driver.current_url.lower()
        if "login" not in current_url and "anmeldung" not in current_url:
            logger.info("✓ Login erfolgreich!")
            return True
        else:
            # Prüfe auf Fehlermeldung
            try:
                error_elem = driver.find_element(By.ID, "uiLoginError")
                if error_elem.is_displayed():
                    logger.error("✗ Login fehlgeschlagen - Falsche Zugangsdaten?")
                    return False
            except:
                pass
            
            logger.warning("Login-Status unklar, versuche fortzufahren...")
            return True
            
    except TimeoutException:
        logger.info("Kein Login-Formular gefunden - bereits eingeloggt?")
        return True
    except Exception as e:
        logger.error(f"Login-Fehler: {e}")
        return False

def wait_for_mesh_rendering(driver, timeout=20):
    """Wartet bis die Mesh-Visualisierung vollständig gerendert wurde"""
    logger.info("Warte auf Mesh-Rendering...")
    
    start_time = time.time()
    
    # Warte auf js3-view Element
    try:
        js3_view = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "js3-view.js3-view--initialized"))
        )
        logger.info("✓ js3-view Element gefunden")
    except TimeoutException:
        logger.warning("js3-view nicht gefunden, versuche trotzdem...")
    
    # Warte zusätzlich auf Canvas oder SVG Elemente (die Mesh-Visualisierung)
    wait_time = 0
    max_wait = timeout
    check_interval = 0.5
    
    while wait_time < max_wait:
        time.sleep(check_interval)
        wait_time += check_interval
        
        # Prüfe auf verschiedene Rendering-Indikatoren
        try:
            # Suche nach Canvas (wird oft für Mesh-Darstellung genutzt)
            canvas_elements = driver.find_elements(By.TAG_NAME, "canvas")
            
            # Suche nach SVG
            svg_elements = driver.find_elements(By.TAG_NAME, "svg")
            
            # Suche nach spezifischen Mesh-Elementen
            mesh_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='mesh']")
            
            if canvas_elements or svg_elements or len(mesh_elements) > 3:
                # Warte noch ein bisschen für vollständiges Rendering
                time.sleep(2)
                logger.info(f"✓ Mesh-Elemente gefunden nach {wait_time:.1f}s")
                logger.info(f"  - Canvas: {len(canvas_elements)}, SVG: {len(svg_elements)}, Mesh-Elemente: {len(mesh_elements)}")
                return True
                
        except Exception as e:
            logger.debug(f"Render-Check Fehler: {e}")
    
    logger.warning(f"Mesh-Rendering-Check abgelaufen nach {max_wait}s - mache trotzdem Screenshot")
    return False

def navigate_to_mesh(driver):
    """Navigiert zur Mesh-Übersicht"""
    
    # Direkte Mesh-URL
    mesh_url = f"{FRITZ_URL}/#/mesh"
    
    logger.info(f"Navigiere zu Mesh-Seite: {mesh_url}")
    driver.get(mesh_url)
    
    # Warte kurz auf Seitenladung
    time.sleep(3)
    
    # Prüfe ob wir auf der richtigen Seite sind
    current_url = driver.current_url
    logger.info(f"Aktuelle URL: {current_url}")
    
    # Warte auf vollständiges Rendering
    wait_for_mesh_rendering(driver)
    
    return True

def take_screenshot(driver):
    """Erstellt einen Screenshot der Mesh-Übersicht"""
    try:
        # Scrolle zum Anfang
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.3)
        
        # Versuche nur den relevanten Bereich zu screenshotten
        try:
            # Suche nach dem Mesh-Container
            mesh_container = driver.find_element(By.CSS_SELECTOR, "js3-view")
            
            # Screenshot des Elements
            mesh_container.screenshot(SCREENSHOT_PATH)
            logger.debug("✓ Element-Screenshot erstellt")
            return True
        except:
            # Fallback: Vollständiger Screenshot
            driver.save_screenshot(SCREENSHOT_PATH)
            logger.debug("✓ Vollständiger Screenshot erstellt")
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
            # Driver erstellen
            if driver is None:
                logger.info("=" * 60)
                logger.info("Erstelle neuen Chrome-Driver...")
                driver = get_driver()
                consecutive_errors = 0
            
            # Zur FritzBox navigieren
            logger.info(f"Öffne FritzBox: {FRITZ_URL}")
            driver.get(FRITZ_URL)
            time.sleep(3)
            
            # Login durchführen
            if not perform_login(driver):
                logger.error("✗ Login fehlgeschlagen!")
                raise Exception("Login failed")
            
            # Zur Mesh-Seite navigieren
            if not navigate_to_mesh(driver):
                logger.error("✗ Mesh-Navigation fehlgeschlagen!")
                raise Exception("Mesh navigation failed")
            
            # Screenshot-Loop
            logger.info("=" * 60)
            logger.info(f"✓ Bereit! Screenshot-Loop gestartet (alle {REFRESH_RATE}s)")
            logger.info("=" * 60)
            
            screenshot_count = 0
            session_start = time.time()
            last_refresh = time.time()
            
            while True:
                # Session-Refresh alle 30 Minuten
                if time.time() - session_start > 1800:
                    logger.info("⟳ Session-Refresh nach 30 Minuten")
                    break
                
                # Seite alle 5 Minuten neu laden (gegen JavaScript-Fehler)
                if time.time() - last_refresh > 300:
                    logger.info("⟳ Seite wird neu geladen...")
                    driver.refresh()
                    time.sleep(3)
                    wait_for_mesh_rendering(driver, timeout=15)
                    last_refresh = time.time()
                
                # Prüfe ob Session noch gültig
                current_url = driver.current_url.lower()
                if "login" in current_url or "anmeldung" in current_url:
                    logger.warning("⚠ Session abgelaufen, starte neu...")
                    break
                
                # Screenshot erstellen
                if take_screenshot(driver):
                    screenshot_count += 1
                    if screenshot_count == 1:
                        logger.info("✓ Erster Screenshot erfolgreich erstellt!")
                    elif screenshot_count % 20 == 0:
                        logger.info(f"ℹ {screenshot_count} Screenshots erstellt (läuft seit {int(time.time()-session_start)}s)")
                    consecutive_errors = 0
                else:
                    consecutive_errors += 1
                    if consecutive_errors >= max_errors:
                        logger.error("✗ Zu viele Screenshot-Fehler, starte Browser neu")
                        break
                
                # Warte bis zum nächsten Screenshot
                time.sleep(REFRESH_RATE)
                
        except WebDriverException as e:
            logger.error(f"✗ WebDriver-Fehler: {e}")
            consecutive_errors += 1
        except Exception as e:
            logger.error(f"✗ Unerwarteter Fehler: {e}")
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
            logger.error(f"⚠ Zu viele Fehler ({consecutive_errors}), warte 60s...")
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
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                padding: 20px;
                max-width: 95vw;
                width: 100%;
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
                min-height: 400px;
                background: #f5f5f5;
                border-radius: 10px;
                padding: 10px;
            }}
            img {{ 
                max-width: 100%; 
                height: auto;
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
            .indicator {{
                display: inline-block;
                width: 8px;
                height: 8px;
                background: #4CAF50;
                border-radius: 50%;
                margin-right: 5px;
                animation: pulse 2s infinite;
            }}
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.3; }}
            }}
        </style>
        <script>
            var refreshRate = {REFRESH_RATE};
            var lastUpdate = new Date();
            var imageLoaded = false;
            
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
            
            // Fehlerbehandlung
            window.addEventListener('load', function() {{
                var img = document.getElementById('mesh-img');
                
                img.onload = function() {{
                    imageLoaded = true;
                }};
                
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
                <span class="indicator"></span>
                Automatische Aktualisierung alle {REFRESH_RATE} Sekunden
            </div>
            <div class="image-wrapper">
                <img id="mesh-img" src="/mesh.png" alt="Lade Mesh Übersicht..." 
                     onerror="this.alt='Bild wird geladen, bitte warten...'">
            </div>
            <div class="last-update" id="last-update">Initialisiere...</div>
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
                        max_age=0,
                        add_etags=False)
    else:
        return "Bild wird generiert, bitte warten...", 503

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
    logger.info("=" * 60)
    logger.info("Fritz!Box Mesh Overview v2.0")
    logger.info("=" * 60)
    logger.info(f"FritzBox URL: {FRITZ_URL}")
    logger.info(f"Benutzer: {FRITZ_USER if FRITZ_USER else 'Standard'}")
    logger.info(f"Refresh Rate: {REFRESH_RATE}s")
    logger.info(f"Passwort gesetzt: {'✓ Ja' if FRITZ_PASS else '✗ NEIN - BITTE SETZEN!'}")
    logger.info("=" * 60)
    
    # Browser-Thread starten
    thread = threading.Thread(target=browser_loop, daemon=True)
    thread.start()
    
    # Flask-Server starten
    logger.info("Starte Webserver auf Port 8000...")
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
