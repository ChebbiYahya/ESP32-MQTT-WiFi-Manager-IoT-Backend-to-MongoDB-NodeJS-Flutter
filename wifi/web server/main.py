try:
    import usocket as socket  # Essaye d'importer usocket pour la gestion des sockets (recommandé pour MicroPython)
except:
    import socket  # Si l'importation de usocket échoue, utilise le socket standard

from machine import Pin  # Importation de la classe Pin pour contrôler les broches GPIO (entrées/sorties) de l'ESP32

import esp  # Importation du module esp pour accéder aux fonctionnalités spécifiques de l'ESP32
esp.osdebug(None)  # Désactive les messages de débogage d'ESP32

import gc  # Importation du module gc pour gérer la collecte de mémoire
gc.collect()  # Lance immédiatement la collecte de la mémoire (libère la mémoire inutilisée)

led = Pin(2, Pin.OUT)  # Crée un objet Pin pour contrôler la broche GPIO numéro 2 (souvent utilisée pour une LED). La broche est configurée en mode "sortie" (Pin.OUT)


def web_page():
    if led.value() == 1:  # Vérifie si la LED est allumée (valeur 1 signifie que la broche est alimentée)
        gpio_state = "ON"  # Si la LED est allumée, défini l'état GPIO à "ON"
    else:
        gpio_state = "OFF"  # Si la LED est éteinte, défini l'état GPIO à "OFF"

    # Génère le code HTML pour afficher l'état de la LED et les boutons pour la contrôler
    html = """<html><head> <title>ESP Web Server</title> <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" href="data:,"> <style>html{font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}
    h1{color: #0F3376; padding: 2vh;}p{font-size: 1.5rem;}.button{display: inline-block; background-color: #e7bd3b; border: none; 
    border-radius: 4px; color: white; padding: 16px 40px; text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
    .button2{background-color: #4286f4;}</style></head><body> <h1>ESP Web Server</h1> 
    <p>GPIO state: <strong>""" + gpio_state + """</strong></p><p><a href="/?led=on"><button class="button">ON</button></a></p>
    <p><a href="/?led=off"><button class="button button2">OFF</button></a></p></body></html>"""  # Création du code HTML
    return html  # Retourne la page HTML générée

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Crée un objet socket en utilisant le protocole IPv4 (AF_INET) et le mode TCP (SOCK_STREAM)
s.bind(('', 80))  # Lie le socket à l'adresse IP locale ('') et au port 80, qui est le port standard pour les requêtes HTTP
s.listen(5)  # Met le serveur en mode écoute, acceptant jusqu'à 5 connexions en attente

while True:  # Boucle infinie pour traiter continuellement les connexions des clients
    conn, addr = s.accept()  # Accepte une connexion entrante. 'conn' est la connexion et 'addr' est l'adresse du client
    print('Got a connection from %s' % str(addr))  # Affiche l'adresse du client qui s'est connecté
    request = conn.recv(1024)  # Reçoit jusqu'à 1024 octets de la requête HTTP envoyée par le client
    request = str(request)  # Convertit les données reçues en chaîne de caractères
    print('Content = %s' % request)  # Affiche la requête reçue pour le débogage

    led_on = request.find('/?led=on')  # Cherche la chaîne "/?led=on" dans la requête pour savoir si l'utilisateur veut allumer la LED
    led_off = request.find('/?led=off')  # Cherche la chaîne "/?led=off" dans la requête pour savoir si l'utilisateur veut éteindre la LED

    if led_on == 6:  # Si "/?led=on" est trouvé dans la requête (c'est-à-dire que la LED doit être allumée)
        print('LED ON')  # Affiche "LED ON" pour indiquer que la LED sera allumée
        led.value(1)  # Allume la LED en mettant la broche à une valeur haute (1)

    if led_off == 6:  # Si "/?led=off" est trouvé dans la requête (c'est-à-dire que la LED doit être éteinte)
        print('LED OFF')  # Affiche "LED OFF" pour indiquer que la LED sera éteinte
        led.value(0)  # Éteint la LED en mettant la broche à une valeur basse (0)

    response = web_page()  # Appelle la fonction web_page() pour générer la page HTML à renvoyer au client
    conn.send('HTTP/1.1 200 OK\n')  # Envoie l'en-tête HTTP pour indiquer que la requête a été traitée avec succès (code 200 OK)
    conn.send('Content-Type: text/html\n')  # Indique que le contenu de la réponse est en HTML
    conn.send('Connection: close\n\n')  # Indique que la connexion sera fermée après l'envoi de la réponse
    conn.sendall(response)  # Envoie la page HTML générée en réponse à la requête du client
    conn.close()  # Ferme la connexion avec le client après avoir envoyé la réponse