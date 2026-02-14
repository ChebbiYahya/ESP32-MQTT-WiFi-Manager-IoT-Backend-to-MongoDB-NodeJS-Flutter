import network                              # Importer le module réseau (Wi-Fi)

ap = network.WLAN(network.AP_IF)            # Créer un objet Wi-Fi en mode Point d’Accès (AP)
ap.active(True)                             # Activer le point d’accès

ap.config(essid='MicroPython-AP', password='123456789')  # Définir le nom du Wi-Fi et le mot de passe

print('AP actif:', ap.ifconfig())           # Afficher les informations du point d’accès (IP, masque, etc.)
