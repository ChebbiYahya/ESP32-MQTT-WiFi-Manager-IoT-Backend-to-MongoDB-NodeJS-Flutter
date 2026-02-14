import network  # Importation du module network qui permet de gérer les connexions réseau sur l'ESP32

ssid = 'Null'  # Définition du nom du réseau Wi-Fi (SSID) auquel on veut se connecter
password = 'yahya123'  # Définition du mot de passe du réseau Wi-Fi

station = network.WLAN(network.STA_IF)  # Création de l'interface réseau en mode station (STA_IF), ce qui signifie que l'ESP32 va se connecter à un réseau Wi-Fi existant

station.active(True)  # Activation de l'interface WLAN en mode station (cela permet à l'ESP32 de tenter de se connecter à un réseau)

station.connect(ssid, password)  # Tentative de connexion à un réseau Wi-Fi en utilisant le SSID et le mot de passe définis précédemment

# Boucle infinie qui attend que l'ESP32 soit connecté au réseau Wi-Fi
while station.isconnected() == False:
  pass  # Tant que l'ESP32 n'est pas connecté, cette boucle vide permet d'attendre

print('Connection successful')  # Lorsque la connexion est établie, un message est affiché pour indiquer que la connexion a réussi

print(station.ifconfig())  # Affiche la configuration réseau de l'ESP32, notamment l'adresse IP, le masque de sous-réseau et la passerelle