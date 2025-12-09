# 📡 Fritz Mesh für Home Assistant

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg) ![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Addon-brightgreen.svg)

Ein **Home Assistant Add-on**, das die Mesh-Übersicht deiner Fritz!Box nahtlos in dein Dashboard integriert.

![Fritz Mesh Screenshot](https://github.com/Lamarqe/fritzmesh/raw/main/fritzmesh_addon/screenshot.jpg)

---

## ✨ Features

Dieses Add-on holt nicht einfach nur die Webseite, sondern optimiert sie für die Darstellung in Home Assistant:

* **🖥️ Fullscreen Optimierung:** CSS- und JS-Parameter werden automatisch angepasst, damit die Übersicht unabhängig von der Auflösung im Vollbildmodus erscheint.
* **⏱️ Live-Updates:** Der Mesh-Status wird alle **5 Sekunden** automatisch aktualisiert.

---

## 🚀 Installation

Folge diesen Schritten, um das Add-on zu installieren:

1.  Gehe in deinem Home Assistant zu **Einstellungen** -> **Add-ons** -> **Add-on Store**.
2.  Klicke oben rechts auf die drei Punkte (`...`) und wähle **Repositories**.
3.  Füge folgende URL als neues Repository hinzu:
    ```text
    [https://github.com/Lamarqe/fritzmesh](https://github.com/Lamarqe/fritzmesh)
    ```
4.  Lade die Seite neu oder suche nach **Fritz Mesh** und installiere das Add-on.
5.  **Wichtig:** Bevor du das Add-on startest, konfiguriere die Zugangsdaten (siehe unten).
6.  Aktiviere die Option **"In der Seitenleiste anzeigen"**, um den neuen Menüpunkt `Netzwerk` zu erhalten.

---

## ⚙️ Konfiguration

Die Konfiguration erfolgt direkt im "Konfiguration"-Tab des Add-ons.

| Parameter | Beschreibung |
| :--- | :--- |
| `Fritzbox username` | Der Benutzername für den Login auf deiner Fritz!Box. |
| `Fritzbox password` | Das zugehörige Passwort. |
| `fritzbox host` | Hostname oder IP-Adresse deiner Fritz!Box.<br>**Standard:** `fritz.box` (funktioniert in den meisten Setups). |

> **💡 Sicherheits-Tipp:**
> Erstelle in deiner Fritz!Box am besten einen **separaten Benutzer** ohne weitreichende Berechtigungen, der nur für dieses Add-on genutzt wird. So bleibt dein Admin-Konto geschützt.

---

Made with ❤️ for Home Assistant