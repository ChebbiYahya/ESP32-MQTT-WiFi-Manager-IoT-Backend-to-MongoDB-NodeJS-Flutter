import wifimgr  # Importe la gestion du Wi-Fi pour se connecter à un réseau
from time import sleep  # Importe la fonction sleep pour faire des pauses
import machine  # Importe le module machine pour accéder aux fonctions matérielles

# Tentative d'importation de la bibliothèque usocket pour une meilleure compatibilité avec les sockets
try:
    import usocket as socket  # Tente d'importer usocket
except:
    import socket  # Si échec, importe socket standard

# Initialise une broche GPIO pour contrôler une LED sur la carte ESP32
led = machine.Pin(2, machine.Pin.OUT)  # La LED est connectée à la broche 2 et est configurée en sortie

# Essaie de se connecter au réseau Wi-Fi via la fonction get_connection de wifimgr
wlan = wifimgr.get_connection()  
if wlan is None:  # Si la connexion échoue
    print("Could not initialize the network connection.")  # Affiche un message d'erreur
    while True:  # Rentre dans une boucle infinie pour arrêter l'exécution
        pass  # Empêche le programme de continuer

# Code principal, ici wlan contient une instance fonctionnelle du réseau Wi-Fi (WLAN(STA_IF))
print("ESP OK")  # Affiche un message indiquant que la connexion Wi-Fi a réussi

# Fonction qui génère la page web que l'utilisateur verra
def web_page():
    if led.value() == 1:  # Si la LED est allumée
        gpio_state = "ON"  # Met la variable gpio_state à "ON"
    else:
        gpio_state = "OFF"  # Si la LED est éteinte, met gpio_state à "OFF"

    # Génère un code HTML pour afficher l'état de la LED et des boutons pour la contrôler
    html = """<html><head> <title>ESP Web Server</title> <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" href="data:,"><style>html{font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}
    h1{color: #0F3376; padding: 2vh;}p{font-size: 1.5rem;}.button{display: inline-block; background-color: #e7bd3b; border: none; 
    border-radius: 4px; color: white; padding: 16px 40px; text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
    .button2{background-color: #4286f4;}</style></head><body> <h1>ESP Web Server</h1> 
    <p>GPIO state: <strong>""" + gpio_state + """</strong></p><p><a href="/?led=on"><button class="button">ON</button></a></p>
    <p><a href="/?led=off"><button class="button button2">OFF</button></a></p></body></html>"""
    return html  # Retourne le code HTML généré

# Tentative de création et configuration d'un serveur socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Crée un socket TCP/IP
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permet de réutiliser l'adresse immédiatement
    s.bind(('', 80))  # Lie le socket à l'adresse IP et au port 80 (HTTP)
    s.listen(5)  # Met le serveur en mode écoute avec une file d'attente de 5 connexions
except OSError as e:  # En cas d'erreur, réinitialise la machine
    machine.reset()

# Boucle principale où le serveur attend et gère les connexions
while True:
    try:
        # Si la mémoire libre est inférieure à 102000, lance le ramassage des ordures pour libérer de la mémoire
        if gc.mem_free() < 102000:
            gc.collect()

        conn, addr = s.accept()  # Accepte la connexion entrante et récupère l'adresse de l'utilisateur
        conn.settimeout(3.0)  # Définit un délai d'attente de 3 secondes pour la connexion
        print('Got a connection from %s' % str(addr))  # Affiche l'adresse de la connexion
        request = conn.recv(1024)  # Reçoit la requête HTTP envoyée par l'utilisateur
        conn.settimeout(None)  # Annule le délai d'attente sur la connexion
        request = str(request)  # Convertit la requête en chaîne de caractères
        print('Content = %s' % request)  # Affiche le contenu de la requête

        # Cherche des commandes spécifiques dans la requête (pour allumer ou éteindre la LED)
        led_on = request.find('/?led=on')  # Cherche "/?led=on"
        led_off = request.find('/?led=off')  # Cherche "/?led=off"

        if led_on == 6:  # Si la requête contient "/?led=on"
            print('LED ON')  # Affiche "LED ON"
            led.value(1)  # Allume la LED
        if led_off == 6:  # Si la requête contient "/?led=off"
            print('LED OFF')  # Affiche "LED OFF"
            led.value(0)  # Éteint la LED

        # Envoie la page HTML générée au client
        response = web_page()
        conn.send('HTTP/1.1 200 OK\n')  # Envoie l'en-tête HTTP
        conn.send('Content-Type: text/html\n')  # Définit le type de contenu comme HTML
        conn.send('Connection: close\n\n')  # Indique que la connexion sera fermée après la réponse
        conn.sendall(response)  # Envoie le corps de la réponse (page HTML)
        conn.close()  # Ferme la connexion

    except OSError as e:  # Si une erreur OSError survient, ferme la connexion
        conn.close()
        print('Connection closed')  # Affiche que la connexion a été fermée