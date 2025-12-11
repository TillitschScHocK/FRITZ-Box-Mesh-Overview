#!/usr/bin/env python3
"""
Fritz!Box Mesh Overview - Live Interactive Proxy
Kompatibel mit FritzOS 8.0+ (Javascript-obfuskiert)
Steuere die Fritz!Box direkt in Home Assistant
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
import json

# ============== KONFIGURATION ==============
FRITZ_HOST = os.getenv("FRITZ_HOST", "fritz.box")
FRITZ_PASS = os.getenv("FRITZ_PASS", "")
FRITZ_USER = os.getenv("FRITZ_USER", "Admin")

# URL konstruieren
if not FRITZ_HOST.startswith(("http://", "https://")):
    FRITZ_URL = f"http://{FRITZ_HOST}"
else:
    FRITZ_URL = FRITZ_HOST

# Pfade
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

# Globale Browser-Session (wird wiederverwendet)
browser_session = {
    "page": None,
    "context": None,
    "browser": None,
    "logged_in": False
}


# ============== BROWSER INITIALIZATION ==============
async def init_browser():
    """Initialisiert den Browser und loggt sich ein"""
    try:
        if browser_session["page"]:
            return True  # Bereits initialisiert
        
        logger.info("Initialisiere Browser...")
        p = await async_playwright().start()
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # === LOGIN ===
        logger.info(f"\u00d6ffne Fritz!Box: {FRITZ_URL}")
        await page.goto(FRITZ_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)
        
        # Login wenn n\u00f6tig
        try:
            login_field = await page.query_selector("#uiPassInput")
            if login_field:
                logger.info("Login-Formular gefunden")
                
                # Benutzer w\u00e4hlen
                try:
                    await page.select_option("#uiViewUser", value=FRITZ_USER)
                    logger.info(f"Benutzer '{FRITZ_USER}' ausgew\u00e4hlt")
                    await page.wait_for_timeout(300)
                except:
                    pass
                
                # Passwort eingeben
                logger.info("Gebe Passwort ein...")
                await page.fill("#uiPassInput", FRITZ_PASS)
                await page.wait_for_timeout(500)
                
                # Login-Button klicken
                logger.info("Klicke Login-Button...")
                await page.click("#submitLoginBtn")
                await page.wait_for_timeout(5000)
                logger.info("\u2713 Login erfolgreich")
            else:
                logger.info("Bereits angemeldet")
        except Exception as e:
            logger.error(f"Login-Fehler: {e}")
            raise
        
        # === NAVIGATE TO MESH ===
        mesh_url = f"{FRITZ_URL}/#/mesh"
        logger.info(f"Navigiere zu Mesh: {mesh_url}")
        await page.goto(mesh_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        
        logger.info("\u2713 Browser initialisiert und bereit!")
        
        browser_session["page"] = page
        browser_session["context"] = context
        browser_session["browser"] = browser
        browser_session["logged_in"] = True
        
        return True
    
    except Exception as e:
        logger.error(f"Browser-Initialisierung fehlgeschlagen: {e}")
        return False


def init_browser_sync():
    """Sync-Wrapper f\u00fcr Browser-Initialisierung"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(init_browser())


# ============== FLASK ROUTES ==============
@app.route("/")
def index():
    """Haupt-Webseite mit Live-Proxy"""
    html = """
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Fritz!Box Mesh - Live</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                padding: 10px;
            }
            .container {
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
            }
            h1 {
                color: #333;
                font-size: 20px;
                margin: 0;
            }
            .info {
                color: #666;
                font-size: 12px;
            }
            .status {
                padding: 10px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
            }
            .status.loading {
                background: #fff3cd;
                color: #856404;
            }
            .status.ready {
                background: #d4edda;
                color: #155724;
            }
            .status.error {
                background: #f8d7da;
                color: #721c24;
            }
            .frame-wrapper {
                flex: 1;
                display: flex;
                justify-content: center;
                align-items: center;
                overflow: auto;
                background: #f9f9f9;
                border-radius: 8px;
                position: relative;
            }
            iframe {
                width: 100%;
                height: 100%;
                border: none;
                border-radius: 8px;
            }
            .loading {
                position: absolute;
                text-align: center;
                color: #999;
            }
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 10px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
        <script>
            async function checkStatus() {
                try {
                    const response = await fetch('/api/status');
                    const data = await response.json();
                    
                    const statusEl = document.getElementById('status');
                    const loaderEl = document.getElementById('loader');
                    const iframeEl = document.getElementById('fritz-frame');
                    
                    if (data.status === 'ready') {
                        statusEl.textContent = '✓ Fritz!Box live verf\u00fcgbar';
                        statusEl.className = 'status ready';
                        if (loaderEl) loaderEl.style.display = 'none';
                        if (iframeEl) iframeEl.style.display = 'block';
                    } else if (data.status === 'loading') {
                        statusEl.textContent = '⏱ Verbinde zu Fritz!Box...';
                        statusEl.className = 'status loading';
                        if (loaderEl) loaderEl.style.display = 'flex';
                    } else {
                        statusEl.textContent = '✗ Fehler beim Verbinden';
                        statusEl.className = 'status error';
                    }
                } catch (e) {
                    console.error('Status-Check Fehler:', e);
                }
            }
            
            // Initial check
            checkStatus();
            
            // Periodic check
            setInterval(checkStatus, 2000);
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🌐 Fritz!Box Mesh - Live Steuerung</h1>
            <div class="info">Interaktive Live-Ansicht deiner Fritz!Box</div>
            <div id="status" class="status loading">Verbinde...</div>
            <div class="frame-wrapper">
                <div id="loader" class="loading" style="display: flex; flex-direction: column; align-items: center;">
                    <div class="spinner"></div>
                    <p>Initialisiere Browser...</p>
                </div>
                <iframe id="fritz-frame" src="/view" style="display: none;"></iframe>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route("/view")
async def view():
    """Live-View der Fritz!Box Mesh-Seite via iframe"""
    if not browser_session["logged_in"]:
        if not init_browser_sync():
            return "Fehler beim Verbinden zur Fritz!Box", 500
    
    page = browser_session["page"]
    if not page:
        return "Browser nicht initialisiert", 500
    
    try:
        # Hole den aktuellen HTML-Content
        content = await page.content()
        
        # Injiziere ein Script, das relative Links korrigiert
        inject_script = """
        <script>
        // Korrigiere alle Links zur Fritz!Box
        document.querySelectorAll('a').forEach(a => {
            if (a.href && !a.href.includes('http')) {
                a.href = 'javascript:void(0)';
                a.onclick = function(e) {
                    e.preventDefault();
                    console.log('Link-Klick:', this.href);
                    return false;
                };
            }
        });
        
        // Verhindere externe Requests
        document.querySelectorAll('img, script, link').forEach(el => {
            if (el.src && !el.src.includes('data:')) {
                el.src = '';
            }
            if (el.href && !el.href.includes('data:')) {
                el.href = '';
            }
        });
        </script>
        """
        
        # Injiziere am Ende des body
        content = content.replace('</body>', inject_script + '</body>')
        
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    
    except Exception as e:
        logger.error(f"View-Fehler: {e}")
        return f"Fehler: {e}", 500


@app.route("/api/status")
async def api_status():
    """API-Endpoint für Status-Check"""
    if not browser_session["logged_in"]:
        if init_browser_sync():
            return jsonify({"status": "ready"}), 200
        else:
            return jsonify({"status": "error", "message": "Verbindung fehlgeschlagen"}), 500
    
    if browser_session["page"]:
        return jsonify({"status": "ready"}), 200
    
    return jsonify({"status": "loading"}), 200


@app.route("/api/navigate", methods=["POST"])
async def api_navigate():
    """API zum Navigieren zu einer URL"""
    if not browser_session["page"]:
        return jsonify({"error": "Browser nicht initialisiert"}), 500
    
    try:
        data = request.json
        url = data.get("url")
        
        if not url:
            return jsonify({"error": "URL erforderlich"}), 400
        
        # Stelle sicher, dass die URL von Fritz!Box ist
        if not url.startswith(("http://192.168", "http://fritz.box", "http://", "http://localhost")):
            url = f"{FRITZ_URL}/{url.lstrip('/')}"
        
        page = browser_session["page"]
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1000)
        
        return jsonify({"success": True}), 200
    
    except Exception as e:
        logger.error(f"Navigation-Fehler: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/click", methods=["POST"])
async def api_click():
    """API zum Klicken auf Elemente"""
    if not browser_session["page"]:
        return jsonify({"error": "Browser nicht initialisiert"}), 500
    
    try:
        data = request.json
        selector = data.get("selector")
        
        if not selector:
            return jsonify({"error": "Selector erforderlich"}), 400
        
        page = browser_session["page"]
        await page.click(selector)
        await page.wait_for_timeout(500)
        
        return jsonify({"success": True}), 200
    
    except Exception as e:
        logger.error(f"Click-Fehler: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/fill", methods=["POST"])
async def api_fill():
    """API zum Ausfüllen von Formularfeldern"""
    if not browser_session["page"]:
        return jsonify({"error": "Browser nicht initialisiert"}), 500
    
    try:
        data = request.json
        selector = data.get("selector")
        value = data.get("value")
        
        if not selector or value is None:
            return jsonify({"error": "Selector und value erforderlich"}), 400
        
        page = browser_session["page"]
        await page.fill(selector, value)
        await page.wait_for_timeout(500)
        
        return jsonify({"success": True}), 200
    
    except Exception as e:
        logger.error(f"Fill-Fehler: {e}")
        return jsonify({"error": str(e)}), 500


# ============== MAIN ==============
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Fritz!Box Mesh Overview v3.0 - Live Interactive")
    logger.info("=" * 60)
    logger.info(f"Fritz!Box: {FRITZ_URL}")
    logger.info(f"Benutzer: {FRITZ_USER}")
    logger.info(f"Passwort: {'✓ Gesetzt' if FRITZ_PASS else '✗ NICHT GESETZT'}")
    logger.info("=" * 60)
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
