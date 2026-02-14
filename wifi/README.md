# Wi-Fi ESP32 - Modes, Web Server et WiFi Manager

**Aperçu**
Ce dossier regroupe trois mini-projets MicroPython autour du Wi-Fi sur ESP32 :
- Mode Access Point vs Station.
- Serveur web local pour piloter une LED.
- WiFi Manager pour configurer le réseau via un portail captif.

**Images**
![Mode Access Point](mode_access_station/mode_access.webp)
![Mode Station](mode_access_station/mode_station.webp)
![Web Server ESP32](web%20server/DSC02551.webp)
![WiFi Manager - écran principal](wifi%20manager/main.png)
![WiFi Manager - portail](wifi%20manager/wifimgr.png)

**1) Mode Access Point / Station**
Ce mini-projet montre la différence entre :
- Un ESP32 qui crée son propre réseau Wi-Fi (AP).
- Un ESP32 qui se connecte à un réseau existant (STA).

Fichiers clés :
- `mode_access_station/Mode_access.py` : création d''un point d''accès Wi-Fi.
- `mode_access_station/Mode_Station.py` : connexion à un routeur Wi-Fi.

Configuration :
- `Mode_access.py` → `ap.config(essid=..., password=...)`.
- `Mode_Station.py` → `WIFI_SSID`, `WIFI_PASSWORD`.

**2) Web Server (contrôle LED)**
Un petit serveur web HTTP sur l''ESP32 permet d''allumer/éteindre la LED via un navigateur.

Fichiers clés :
- `web server/boot.py` : connexion Wi-Fi.
- `web server/main.py` : serveur HTTP + page HTML.

Utilisation :
- Charger `boot.py` et `main.py` sur l''ESP32.
- Se connecter au Wi-Fi, récupérer l''IP dans le terminal.
- Ouvrir `http://<ip_esp32>/` et cliquer sur ON/OFF.

**3) WiFi Manager (portail de configuration)**
Si l''ESP32 ne trouve pas de réseau, il crée un AP `WifiManager` et ouvre un portail web pour saisir le SSID et le mot de passe.

Fichiers clés :
- `wifi manager/wifimgr.py` : logique du portail captif et stockage des profils.
- `wifi manager/main.py` : démarre le portail et lance un web server de contrôle LED.

Configuration :
- `wifimgr.py` → `ap_ssid`, `ap_password`.
- Les réseaux enregistrés sont sauvegardés dans `wifi.dat` sur la carte.

**Pré-requis**
- ESP32 avec MicroPython.
- Accès au Wi-Fi local.

**Notes**
- La LED est pilotée sur la broche GPIO 2 dans ces exemples.
- Pensez à adapter les SSID et mots de passe à votre environnement.
