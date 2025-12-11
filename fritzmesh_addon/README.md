# Fritz!Box Mesh Overview - Home Assistant Addon

## 🆕 Beschreibung

Dieses Addon zeigt die Mesh-Übersicht deiner Fritz!Box direkt in Home Assistant an. Es funktioniert auch mit **FritzOS 8.0+**, wo AVM JavaScript-Obfuskierung nutzt.

### ✨ Features

- 🌐 Automatische Screenshot-Erfassung der Mesh-Übersicht
- 🔄 Konfigurierbare Auto-Aktualisierung (5-300 Sekunden)
- 🔓 Sichere Authentifizierung mit Passwort
- 🚀 Schnell und stabil (Playwright statt Selenium)
- 😸 Multi-Benutzer-Unterstützung
- 📊 Web-Interface auf Port 8000

## 💻 Anforderungen

- Home Assistant OS oder Home Assistant mit Docker-Support
- Fritz!Box mit aktuellem FritzOS (7.0+)
- Zugang zur Fritz!Box Web-UI (Standard: http://fritz.box)
- Admin-Passwort der Fritz!Box

## 🛠 Installation

### 1. Repository hinzufügen

Fücge folgende URL als benutzerdefiniertes Repository zu Home Assistant hinzu:

```
https://github.com/TillitschScHocK/FRITZ-Box-Mesh-Overview
```

### 2. Addon installieren

1. Gehe zu **Einstellungen → Add-ons & Integrationen → Add-on Store**
2. Suche nach **Fritz!Box Mesh Overview**
3. Klicke auf **Installieren**
4. Warte auf Completion (ca. 2-3 Minuten)

## ⚙️ Konfiguration

### Erforderliche Einstellungen

| Einstellung | Beschreibung | Standard |
|-------------|-------------|----------|
| **Fritz!Box Host** | IP-Adresse oder Hostname der Fritz!Box | `fritz.box` |
| **Passwort** | Admin-Passwort der Fritz!Box | - |
| **Benutzer** | Benutzername (optional) | `Admin` |
| **Refresh-Rate** | Sekunden zwischen Updates | `10` |

### Beispiel-Konfiguration

```yaml
fritz_host: fritz.box
fritz_pass: dein_passwort
fritz_user: Admin
refresh_rate: 15
```

## 🌟 Zugriff

Nach erfolgreicher Installation:

1. Öffne Home Assistant
2. Gehe zu **Einstellungen → Add-ons & Integrationen**
3. Klicke auf **Fritz!Box Mesh Overview**
4. Klicke auf den Link unter **Web Interface** (Port 8000)

Oder direkt im Browser:
```
http://[YOUR_HOME_ASSISTANT_IP]:8000
```

## 📄 Logs ansehen

So schaust du dir die Logs an:

```
ha supervisor logs --addon 8d5557f1_fritzmesh
```

Oder in der UI:
1. Gehe zu **Einstellungen → Add-ons & Integrationen**
2. Wähle das Addon
3. Scrolle zu **Logs**

## 🔧 Fehlerbehebung

### "Addon konnte nicht installiert werden"

**Lösung:**
- Warte 10 Minuten (Download/Build kann lange dauern)
- Überprüfe Docker-Speicher: `ha docker stats`
- Starte Home Assistant neu

### "Weiße Seite / Kein Screenshot"

**Lösungen:**
1. Passwort korrekt?
   - Teste manuell: `http://fritz.box`
   - Prüfe ob Login funktioniert

2. Fritz!Box erreichbar?
   ```bash
   ping fritz.box
   ```

3. Logs prüfen:
   ```bash
   ha supervisor logs --addon 8d5557f1_fritzmesh
   ```

### "Login fehlgeschlagen"

**Prüfe:**
- Passwort ist korrekt
- Benutzer existiert auf Fritz!Box
- Fritz!Box nicht gesperrt (3x falsches PW)

## 📇 Versionshistorie

### v2.1.0 (Aktuell)
- 🆕 Playwright statt Selenium (schneller, stabiler)
- 🚀 Deutlich schnelleres Docker-Build
- 🔓 Bessere Fehlerbehandlung

### v2.0.0
- Initiale Selenium-Implementierung
- FritzOS 8.0+ Unterstützung

## 📝 Lizenz

MIT License - Siehe LICENSE Datei

## 🙋 Support

Bei Problemen:

1. Überprüfe die Logs
2. Öffne ein Issue auf GitHub
3. Beschreibe dein Problem detailliert

---

**Fritz!Box kompatibel:** 7.0+  
**FritzOS kompatibel:** 6.0 - 8.x  
**Home Assistant:** 2024.1+
