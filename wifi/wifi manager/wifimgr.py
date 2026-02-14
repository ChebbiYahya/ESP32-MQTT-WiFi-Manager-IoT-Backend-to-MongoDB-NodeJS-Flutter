import network  # Importation du module pour gérer les connexions réseau (Wi-Fi)
import socket  # Importation du module pour gérer les connexions réseau avec des clients (serveur)
import ure  # Importation de module pour utiliser des expressions régulières (recherche dans des chaînes de caractères)
import time  # Importation du module pour gérer le temps (attente entre certaines actions)

# Définition des paramètres pour le point d'accès Wi-Fi
ap_ssid = "WifiManager"  # Le nom du réseau Wi-Fi (SSID) pour le point d'accès
ap_password = "formation"  # Le mot de passe pour accéder au réseau Wi-Fi
ap_authmode = 3  # Mode de sécurité du réseau Wi-Fi (ici WPA2)
NETWORK_PROFILES = 'wifi.dat'  # Fichier qui contiendra les profils de réseau enregistrés (SSID et mot de passe)

# Création d'instances pour gérer les interfaces Wi-Fi : point d'accès (AP) et station (STA)
wlan_ap = network.WLAN(network.AP_IF)  # Interface pour le point d'accès (AP)
wlan_sta = network.WLAN(network.STA_IF)  # Interface pour la station (STA) qui se connecte à un réseau

server_socket = None  # Initialisation du socket du serveur à None

def get_connection():
    """Retourne une instance fonctionnelle de WLAN(STA_IF) ou None si impossible de se connecter"""
    
    # Vérification si une connexion Wi-Fi existe déjà
    if wlan_sta.isconnected():
        return wlan_sta  # Retourne l'instance de station Wi-Fi si déjà connecté

    connected = False
    try:
        # Attendre un peu pour que la connexion Wi-Fi soit établie
        time.sleep(3)
        if wlan_sta.isconnected():
            return wlan_sta  # Si la connexion est établie après l'attente, retourne l'instance

        # Lire les profils réseau enregistrés dans un fichier
        profiles = read_profiles()

        # Recherche des réseaux Wi-Fi disponibles à proximité
        wlan_sta.active(True)  # Active le mode station (STA) pour la recherche de réseaux
        networks = wlan_sta.scan()  # Lance une recherche des réseaux Wi-Fi disponibles

        # Dictionnaire pour les modes d'authentification des réseaux
        AUTHMODE = {0: "open", 1: "WEP", 2: "WPA-PSK", 3: "WPA2-PSK", 4: "WPA/WPA2-PSK"}
        
        # Parcours des réseaux trouvés, triés par puissance du signal (rssi)
        for ssid, bssid, channel, rssi, authmode, hidden in sorted(networks, key=lambda x: x[3], reverse=True):
            ssid = ssid.decode('utf-8')  # Décode le SSID du réseau
            encrypted = authmode > 0  # Vérifie si le réseau est crypté
            print("ssid: %s chan: %d rssi: %d authmode: %s" % (ssid, channel, rssi, AUTHMODE.get(authmode, '?')))
            
            # Si le réseau est crypté, essaie de se connecter avec le mot de passe enregistré
            if encrypted:
                if ssid in profiles:
                    password = profiles[ssid]
                    connected = do_connect(ssid, password)
                else:
                    print("skipping unknown encrypted network")  # Ignorer les réseaux cryptés inconnus
            else:  # Si le réseau est ouvert (pas de mot de passe)
                connected = do_connect(ssid, None)
            
            if connected:
                break  # Si une connexion réussie est établie, sortir de la boucle

    except OSError as e:
        print("exception", str(e))  # Affiche l'exception en cas d'erreur

    # Si aucune connexion n'a été établie, démarre un serveur web pour permettre à l'utilisateur de se connecter manuellement
    if not connected:
        connected = start()

    return wlan_sta if connected else None  # Retourne l'instance de station si connecté, sinon None

def read_profiles():
    """Lit les profils de réseau enregistrés depuis le fichier"""
    with open(NETWORK_PROFILES) as f:  # Ouvre le fichier des profils réseau
        lines = f.readlines()  # Lit toutes les lignes du fichier
    profiles = {}
    for line in lines:
        ssid, password = line.strip("\n").split(";")  # Sépare le SSID et le mot de passe
        profiles[ssid] = password  # Ajoute le profil au dictionnaire
    return profiles  # Retourne le dictionnaire des profils

def write_profiles(profiles):
    """Écrit les profils de réseau dans le fichier"""
    lines = []
    for ssid, password in profiles.items():  # Parcours des profils
        lines.append("%s;%s\n" % (ssid, password))  # Formate chaque profil sous forme "SSID;mot_de_passe"
    with open(NETWORK_PROFILES, "w") as f:
        f.write(''.join(lines))  # Écrit tous les profils dans le fichier

def do_connect(ssid, password):
    """Tente de se connecter à un réseau Wi-Fi avec un SSID et un mot de passe"""
    wlan_sta.active(True)  # Active l'interface station pour se connecter au réseau
    if wlan_sta.isconnected():
        return None  # Si déjà connecté, ne fait rien
    print('Trying to connect to %s...' % ssid)  # Affiche que l'on tente de se connecter
    wlan_sta.connect(ssid, password)  # Lance la connexion au réseau avec les informations fournies
    for retry in range(200):  # Essaye jusqu'à 200 fois de se connecter
        connected = wlan_sta.isconnected()
        if connected:  # Si la connexion réussit, on sort de la boucle
            break
        time.sleep(0.1)  # Attend 0.1 seconde avant de réessayer
        print('.', end='')  # Affiche un point pour chaque tentative
    if connected:
        print('\nConnected. Network config: ', wlan_sta.ifconfig())  # Affiche l'adresse du réseau connecté
    else:
        print('\nFailed. Not Connected to: ' + ssid)  # Si échec de connexion
    return connected  # Retourne True si connecté, sinon False

def send_header(client, status_code=200, content_length=None):
    """Envoie l'en-tête HTTP de la réponse"""
    client.sendall("HTTP/1.0 {} OK\r\n".format(status_code))  # Envoie le code de statut HTTP (ex: 200 OK)
    client.sendall("Content-Type: text/html\r\n")  # Indique que le contenu est en HTML
    if content_length is not None:  # Si la longueur du contenu est spécifiée
        client.sendall("Content-Length: {}\r\n".format(content_length))  # Envoie la longueur du contenu
    client.sendall("\r\n")  # Envoie une ligne vide pour terminer l'en-tête

def send_response(client, payload, status_code=200):
    """Envoie la réponse HTTP complète au client"""
    content_length = len(payload)  # Calcule la longueur du contenu (corps de la réponse)
    send_header(client, status_code, content_length)  # Envoie l'en-tête
    if content_length > 0:
        client.sendall(payload)  # Envoie le corps de la réponse
    client.close()  # Ferme la connexion après l'envoi de la réponse

def handle_root(client):
    """Gère la page d'accueil (racine) pour afficher les réseaux Wi-Fi disponibles"""
    wlan_sta.active(True)  # Active l'interface station pour rechercher les réseaux
    ssids = sorted(ssid.decode('utf-8') for ssid, *_ in wlan_sta.scan())  # Recherche et trie les SSID
    send_header(client)  # Envoie l'en-tête HTTP
    client.sendall("""<html> ... </html>""")  # Envoie le code HTML pour afficher les réseaux disponibles
    client.close()  # Ferme la connexion

def handle_configure(client, request):
    """Gère la page de configuration pour saisir le SSID et le mot de passe"""
    match = ure.search("ssid=([^&]*)&password=(.*)", request)  # Cherche le SSID et le mot de passe dans la requête

    if match is None:
        send_response(client, "Parameters not found", status_code=400)  # Si les paramètres sont manquants, renvoie une erreur
        return False
    try:
        # Décodage des paramètres SSID et mot de passe
        ssid = match.group(1).decode("utf-8").replace("%3F", "?").replace("%21", "!")
        password = match.group(2).decode("utf-8").replace("%3F", "?").replace("%21", "!")
    except Exception:
        ssid = match.group(1).replace("%3F", "?").replace("%21", "!")
        password = match.group(2).replace("%3F", "?").replace("%21", "!")

    if len(ssid) == 0:
        send_response(client, "SSID must be provided", status_code=400)  # Si le SSID est manquant, renvoie une erreur
        return False

    if do_connect(ssid, password):  # Si la connexion est réussie
        response = """\
            <html>
                <center>
                    <br><br>
                    <h1 style="color: #5e9ca0; text-align: center;">
                        <span style="color: #ff0000;">
                            ESP successfully connected to WiFi network %(ssid)s.
                        </span>
                    </h1>
                    <br><br>
                </center>
            </html>
        """ % dict(ssid=ssid)  # Réponse HTML indiquant que la connexion a réussi
        send_response(client, response)  # Envoie la réponse
        time.sleep(1)  # Attend une seconde
        wlan_ap.active(False)  # Désactive le point d'accès
        try:
            profiles = read_profiles()  # Lit les profils enregistrés
        except OSError:
            profiles = {}
        profiles[ssid] = password  # Enregistre le SSID et le mot de passe
        write_profiles(profiles)  # Sauvegarde les profils dans le fichier

        time.sleep(5)  # Attend 5 secondes avant de revenir

        return True
    else:
        response = """\
            <html>
                <center>
                    <h1 style="color: #5e9ca0; text-align: center;">
                        <span style="color: #ff0000;">
                            ESP could not connect to WiFi network %(ssid)s.
                        </span>
                    </h1>
                    <br><br>
                    <form>
                        <input type="button" value="Go back!" onclick="history.back()"></input>
                    </form>
                </center>
            </html>
        """ % dict(ssid=ssid)  # Réponse HTML indiquant l'échec de la connexion
        send_response(client, response)  # Envoie la réponse
        return False

def handle_not_found(client, url):
    """Gestion des chemins non trouvés (erreur 404)"""
    send_response(client, "Path not found: {}".format(url), status_code=404)  # Envoie une erreur 404

def stop():
    """Arrête le serveur"""
    global server_socket
    if server_socket:
        server_socket.close()  # Ferme le socket du serveur
        server_socket = None

def start(port=80):
    """Démarre le serveur web sur le port spécifié (par défaut 80)"""
    global server_socket

    addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]  # Récupère l'adresse et le port

    stop()  # Arrête le serveur s'il est déjà en cours d'exécution

    wlan_sta.active(True)  # Active le mode station pour se connecter au réseau
    wlan_ap.active(True)  # Active le point d'accès pour que les utilisateurs puissent se connecter

    wlan_ap.config(essid=ap_ssid, password=ap_password)  # Configure le point d'accès avec SSID et mot de passe

    server_socket = socket.socket()  # Crée un nouveau socket pour le serveur
    server_socket.bind(addr)  # Lie l'adresse et le port au serveur
    server_socket.listen(1)  # Écoute une seule connexion à la fois

    print('Connect to WiFi ssid ' + ap_ssid + ', default password: ' + ap_password)
    print('and access the ESP via your favorite web browser at 192.168.4.1.')
    print('Listening on:', addr)

    while True:
        if wlan_sta.isconnected():  # Si l'ESP est connecté à un réseau Wi-Fi
            wlan_ap.active(False)  # Désactive le point d'accès
            return True

        client, addr = server_socket.accept()  # Accepte une connexion d'un client
        print('client connected from', addr)
        try:
            client.settimeout(5.0)  # Définit un délai d'attente pour la connexion

            request = b""  # Initialisation de la requête vide
            try:
                while "\r\n\r\n" not in request:
                    request += client.recv(512)  # Reçoit les données du client
            except OSError:
                pass

            # Gère les données de formulaire provenant de Safari sur macOS et iOS
            try:
                request += client.recv(1024)  # Reçoit plus de données si nécessaire
                print("Received form data after \\r\\n\\r\\n(i.e. from Safari on macOS or iOS)")
            except OSError:
                pass

            print("Request is: {}".format(request))  # Affiche la requête reçue
            if "HTTP" not in request:  # Ignore les requêtes invalides
                continue

            # Recherche de l'URL dans la requête
            try:
                url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).decode("utf-8").rstrip("/")
            except Exception:
                url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).rstrip("/")
            print("URL is {}".format(url))

            if url == "":  # Si l'URL est vide, affiche la page d'accueil
                handle_root(client)
            elif url == "configure":  # Si l'URL est 'configure', gère la configuration
                handle_configure(client, request)
            else:
                handle_not_found(client, url)  # Si l'URL n'est pas trouvée, renvoie une erreur 404

        finally:
            client.close()  # Ferme la connexion avec le client après traitement