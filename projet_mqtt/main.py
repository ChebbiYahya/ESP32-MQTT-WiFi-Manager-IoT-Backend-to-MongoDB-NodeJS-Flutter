import dht  # Importation du module dht pour gérer les capteurs DHT (DHT11 ou DHT22) pour la mesure de température et d'humidité
import machine  # Importation du module machine pour interagir avec le matériel (GPIO)
import time  # Importation du module time pour gérer les temporisations (attentes)
import ubinascii  # Importation du module ubinascii pour manipuler les données binaires (par exemple, pour l'encodage en base64)
import network  # Importation du module network pour gérer les connexions réseau
from umqtt.simple import MQTTClient  # Importation du module MQTTClient pour la communication avec un broker MQTT

# Configuration du GPIO pour le capteur DHT11
sensor = dht.DHT11(machine.Pin(4))

# Connexion Wi-Fi (remplacez par vos identifiants)
ssid = "Chebbi_WiFi"  # Définition du nom du réseau Wi-Fi auquel se connecter
password = "chebbi123"  # Définition du mot de passe du réseau Wi-Fi

wlan = network.WLAN(network.STA_IF)  # Création de l'interface WLAN en mode station (STA_IF), pour connecter l'ESP32 à un réseau Wi-Fi existant.
wlan.active(False)  # Désactivation initiale de l'interface Wi-Fi
time.sleep(1)  # Attente de 1 seconde pour s'assurer que l'interface est correctement désactivée
wlan.active(True)  # Réactivation de l'interface Wi-Fi
time.sleep(1)  # Attente de 1 seconde pour s'assurer que l'interface est activée

# Vérifie si la connexion Wi-Fi n'est pas encore établie
if not wlan.isconnected():
    wlan.connect(ssid, password)  # Connexion au réseau Wi-Fi avec le SSID et le mot de passe spécifiés
    while not wlan.isconnected():  # Boucle qui attend la connexion Wi-Fi
        time.sleep(0.5)  # Attente de 0.5 seconde avant de vérifier à nouveau la connexion

print("Wi-Fi OK:", wlan.ifconfig()) # Affiche la configuration du réseau (adresse IP, masque de sous-réseau, passerelle, etc.) une fois la connexion réussie

# Configuration du client MQTT
mqtt_broker = "192.168.100.9"  # Définition de l'adresse IP du broker MQTT (le serveur auquel se connecter pour échanger les messages)
mqtt_client_id = ubinascii.b2a_base64(machine.unique_id()).strip()  # Génère un ID unique pour le client MQTT à partir de l'ID unique de la machine, encodé en base64
mqtt_topic = "iot/esp32/sensor_data"  # Définition du sujet (topic) MQTT où les données seront publiées
mqtt_client = MQTTClient(mqtt_client_id, mqtt_broker)  # Création du client MQTT avec l'ID unique du client et l'adresse du broker

# Connexion au broker MQTT
mqtt_client.connect()  # Connexion au broker MQTT avec les informations de connexion définies précédemment

while True:  # Boucle infinie pour lire en continu les données du capteur et les envoyer via MQTT
    try:
        sensor.measure()  # Prend une mesure du capteur DHT11 (température et humidité)
        temperature = sensor.temperature()  # Récupère la température mesurée (en °C)
        humidity = sensor.humidity()  # Récupère l'humidité mesurée (en %)

        # Crée un message formaté en JSON avec les valeurs de température et d'humidité
        message = "{ \"temperature\": " + str(temperature) + ", \"humidity\": " + str(humidity) + " }"
        
        # Publier les données sur le broker MQTT
        mqtt_client.publish(mqtt_topic, message)  # Publie le message (données de température et d'humidité) sur le sujet spécifié du broker MQTT
        print("Données envoyées: ", message)  # Affiche dans la console les données envoyées
        
        time.sleep(10)  # Attendre 10 secondes avant la prochaine mesure
    except Exception as e:
        print("Erreur lors de la lecture du capteur:", e)
        time.sleep(5)
