# Fritz!Box Mesh Overview - Home Assistant Addon

## 🎯 Neu in v3.0: Live Interactive Proxy!

Statt statische Screenshots kannst du deine Fritz!Box jetzt **direkt in Home Assistant steuern**!

✅ **Echte HTML-Steuerung** (nicht nur Bilder)  
✅ **Interaktiv** (klick auf Links, fühle aus, navigiere)  
✅ **Live-Updates** (keine veralteten Screenshots)  
✅ **Persistent Session** (bleibt angemeldet)  
✅ **Vollständig in Home Assistant integriert**

## 📋 Features

- 🔴 **Live Mesh-Übersicht** in echtem HTML (nicht Screenshot!)
- 🎛️ **Voll interaktiv** - klick auf Links, führe Aktionen aus
- 🔄 **Persistent Session** - bleibt angemeldet und bereit
- 📱 **Responsive Design** - funktioniert auf Desktop, Tablet, Mobile
- 🔒 **Sichere Authentifizierung** - nur mit Passwort
- 🚀 **Schnell** - kein Browser-Rendering, echtes HTML
- 🏠 **Vollständig in Home Assistant integriert**

## 🛠️ Anforderungen

- Home Assistant OS oder Home Assistant mit Docker-Support
- Fritz!Box mit FritzOS 7.0+
- Zugang zur Fritz!Box (Standard: http://fritz.box)
- Admin-Passwort

## 📥 Installation

### 1. Repository hinzufügen

Fücge folgende URL zu Home Assistant hinzu:

```
https://github.com/TillitschScHocK/FRITZ-Box-Mesh-Overview
```

### 2. Addon installieren

1. **Einstellungen** → **Add-ons & Integrationen** → **Add-on Store**
2. Suche nach **Fritz!Box Mesh Overview**
3. Klicke **Installieren**
4. Warte auf Completion (ca. 2-3 Min)

## ⚙️ Konfiguration

| Einstellung | Beschreibung | Standard |
|-------------|-------------|----------|
| **fritz_host** | IP/Hostname der Fritz!Box | `fritz.box` |
| **fritz_pass** | Admin-Passwort | - |
| **fritz_user** | Benutzername | `Admin` |

### Beispiel:

```yaml
fritz_host: fritz.box
fritz_pass: dein_passwort
fritz_user: Tilli
```

## 🚀 Benutzung

### Start

1. Konfiguriere wie oben
2. Klicke **Starten**
3. Warte bis Status zeigt: `✓ Fritz!Box live verfügbar`
4. Klicke **OPEN WEB UI** Button

### Web-Interface

```
http://192.168.1.100:8000
```

Du siehst deine Fritz!Box **live und interaktiv** - nicht als Screenshot!

## 🎮 Was du tun kannst

✅ Auf Links klicken  
✅ Formularfelder ausfüllen  
✅ Buttons drücken  
✅ Durch Menüs navigieren  
✅ Einstellungen ändern  
✅ In Echtzeit sehen  

## 🔧 API Endpoints (Optional)

Für erweiterte Nutzung:

### Status prüfen
```bash
curl http://localhost:8000/api/status
# {"status": "ready"}
```

### Zu URL navigieren
```bash
curl -X POST http://localhost:8000/api/navigate \
  -H "Content-Type: application/json" \
  -d '{"url": "http://fritz.box/#/mesh"}'
```

### Element klicken
```bash
curl -X POST http://localhost:8000/api/click \
  -H "Content-Type: application/json" \
  -d '{"selector": "#submitBtn"}'
```

### Formularfeld ausfüllen
```bash
curl -X POST http://localhost:8000/api/fill \
  -H "Content-Type: application/json" \
  -d '{"selector": "#inputField", "value": "Neuer Wert"}'
```

## 📺 Logs ansehen

```bash
ha supervisor logs --addon 8d5557f1_fritzmesh
```

Sollte zeigen:
```
✓ Browser initialisiert und bereit!
✓ Fritz!Box live verfügbar
```

## 🐛 Fehlerbehebung

### "Fehler beim Verbinden"

1. Ist die Fritz!Box unter fritz.box erreichbar?
   ```bash
   ping fritz.box
   ```

2. Passwort korrekt?
   - Teste Login auf http://fritz.box direkt

3. Logs anschauen:
   ```bash
   ha supervisor logs --addon 8d5557f1_fritzmesh
   ```

### "Laden bleibt hängen"

- Addon neu starten
- Home Assistant neu starten
- Prüfe Netzwerk-Verbindung zur Fritz!Box

### "Nur weiße Seite"

- Logs prüfen (siehe oben)
- Browser-Konsole prüfen (F12 im Browser)
- Addon-Logs für Fehler durchsuchen

## 📝 Versionshistorie

### v3.0.0 (Aktuell)
🎉 **Live Interactive Proxy!**
- Echte HTML statt Screenshots
- Vollständig interaktiv
- Persistente Session
- API für erweiterte Nutzung

### v2.2.x
- Stable Screenshot-Version
- Auto-Refresh
- Einfache GUI

## 📄 Lizenz

MIT License - Siehe LICENSE

## 💬 Support

Bei Fragen oder Problemen:
1. Schau in die Logs
2. Erstelle ein Issue auf GitHub
3. Beschreibe dein Problem detailliert

---

**Kompatibilität:**
- Fritz!Box: 7.0+
- FritzOS: 6.0-8.x
- Home Assistant: 2024.1+

**Möchtest du die alte Screenshot-Version?** → Checkout v2.2.x Branch
