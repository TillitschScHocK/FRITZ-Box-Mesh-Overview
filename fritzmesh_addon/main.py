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

# Konfiguration aus Umgebungsvariablen (Home Assistant Standard)
# Falls du config.json nutzt, liest HA diese oft in ENV vars oder wir müssten json parsen.
# Hier nehmen wir einfache ENV Vars an, die du im Docker/HA setzen kannst.
FRITZ_USER = os.getenv("FRITZ_USER", "")  # Oft nicht benötigt bei reinem Passwort-Login
FRITZ_PASS = os.getenv("FRITZ_PASS", "deinPasswort")
FRITZ_URL = os.getenv("FRITZ_HOST", "http://fritz.box")
REFRESH_RATE = int(os.getenv("REFRESH_RATE", "10"))

# Pfad für den Screenshot
SCREENSHOT_PATH = "/app/static/mesh.png"
if not os.path.exists("/app/static"):
    os.makedirs("/app/static")

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Kein GUI
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # Wichtig: User-Agent setzen, damit FritzBox uns nicht blockt
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    # Pfad zum Chromium Driver im Docker
    service = webdriver.chrome.service.Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def browser_loop():
    driver = None
    while True:
        try:
            if driver is None:
                print("Starte Browser...")
                driver = get_driver()
            
            print(f"Öffne {FRITZ_URL}...")
            driver.get(FRITZ_URL)
            
            # 1. Login Versuchen
            try:
                # Warten auf Passwortfeld
                pass_input = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "uiPass"))
                )
                print("Login-Seite erkannt. Logge ein...")
                pass_input.clear()
                pass_input.send_keys(FRITZ_PASS)
                pass_input.send_keys(Keys.RETURN)
                
                # Warten bis Login durch ist (Prüfen auf ein Element der Hauptseite)
                time.sleep(5) 
            except:
                print("Kein Login nötig oder bereits eingeloggt (oder Fehler).")

            # 2. Zur Mesh Seite navigieren
            # Die URL für Mesh hat sich evtl. geändert, wir versuchen den direkten Link oder Hash
            # FritzOS 8 nutzt oft Hash-basiertes Routing
            mesh_url = f"{FRITZ_URL}/#/homeNet/mesh"
            if driver.current_url != mesh_url:
                print("Navigiere zur Mesh-Übersicht...")
                driver.get(mesh_url)
            
            # 3. Loop für Screenshots
            while True:
                # Prüfen, ob wir noch auf der richtigen Seite sind oder rausgeflogen sind
                if "login" in driver.current_url or "homeNet" not in driver.current_url:
                    print("Sitzung verloren, starte neu...")
                    break # Bricht inneren Loop, startet Browser neu
                
                # Warten damit Rendering fertig ist
                time.sleep(2)
                
                # Screenshot machen
                driver.save_screenshot(SCREENSHOT_PATH)
                # print("Screenshot aktualisiert.")
                
                time.sleep(REFRESH_RATE)

        except Exception as e:
            print(f"Browser Fehler: {e}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            driver = None
            time.sleep(10) # Kurz warten vor Neustart

# Hintergrund-Thread starten
thread = threading.Thread(target=browser_loop)
thread.daemon = True
thread.start()

# --- Webserver ---

@app.route('/')
def index():
    # Einfache HTML Seite, die das Bild alle X Sekunden neu lädt
    html = f"""
    <html>
    <head>
        <title>Fritz!Box Mesh Overview</title>
        <style>
            body {{ margin: 0; background: #222; display: flex; justify-content: center; align-items: center; height: 100vh; }}
            img {{ max-width: 100%; max-height: 100%; box-shadow: 0 0 20px rgba(0,0,0,0.5); }}
        </style>
        <script>
            setInterval(function() {{
                var img = document.getElementById('mesh-img');
                img.src = '/mesh.png?t=' + new Date().getTime();
            }}, {REFRESH_RATE * 1000});
        </script>
    </head>
    <body>
        <img id="mesh-img" src="/mesh.png" alt="Lade Mesh Übersicht...">
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/mesh.png')
def get_image():
    if os.path.exists(SCREENSHOT_PATH):
        return send_file(SCREENSHOT_PATH, mimetype='image/png')
    else:
        return "Noch kein Bild verfügbar", 404

if __name__ == '__main__':
    print("Starte Webserver auf Port 8000...")
    app.run(host='0.0.0.0', port=8000)