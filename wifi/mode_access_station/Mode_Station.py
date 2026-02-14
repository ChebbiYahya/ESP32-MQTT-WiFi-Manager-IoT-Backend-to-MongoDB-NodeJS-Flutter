import network                     # Importer le module pour gérer le Wi-Fi

WIFI_SSID = "Null"          # Nom du réseau Wi-Fi (SSID)
WIFI_PASSWORD = "yahya123"# Mot de passe du Wi-Fi (ici, vide)

 
wlan = network.WLAN(network.STA_IF) # Créer un objet Wi-Fi en mode station (STA

wlan.active(True)                   # Activer le Wi-Fi

if not wlan.isconnected():          # Vérifier si l'ESP32 n'est pas déjà connecté
    print("Connecting to WI-FI")    # Afficher un message de connexion
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)  # Se connecter au réseau Wi-Fi
    while not wlan.isconnected():   # Attendre jusqu'à la connexion réussie
        pass
    print("Connected to WI-FI ", wlan.ifconfig())  # Afficher l'adresse IP et infos réseau
