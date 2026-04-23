import dht  # Importation du module dht pour gérer les capteurs DHT (DHT11 ou DHT22) pour la mesure de température et d'humidité
import machine  # Importation du module machine pour interagir avec le matériel (GPIO)
import time  # Importation du module time pour gérer les temporisations (attentes)
import ubinascii  # Importation du module ubinascii pour manipuler les données binaires (par exemple, pour l'encodage en base64)
import network  # Importation du module network pour gérer les connexions réseau
import ujson  # Importation du module JSON pour MicroPython
from umqtt.simple import MQTTClient  # Importation du module MQTTClient pour la communication avec un broker MQTT

# Configuration du GPIO pour le capteur DHT11
sensor = dht.DHT11(machine.Pin(4))

# Configuration du GPIO pour le relais
relay_pin = machine.Pin(2, machine.Pin.OUT)
relay_pin.value(0)  # Relais initialement fermé

# Variable globale pour stocker le dernier message reçu
last_received_message = None

# Connexion Wi-Fi (remplacez par vos identifiants)
ssid = "Chebbi_WiFi"  # Définition du nom du réseau Wi-Fi auquel se connecter
password = "chebbi123"  # Définition du mot de passe du réseau Wi-Fi

# Configuration du client MQTT
mqtt_broker = "192.168.100.9"  # Définition de l'adresse IP du broker MQTT (le serveur auquel se connecter pour échanger les messages)
mqtt_client_id = ubinascii.b2a_base64(machine.unique_id()).strip()  # Génère un ID unique pour le client MQTT à partir de l'ID unique de la machine, encodé en base64
mqtt_sender_topic = "iot/esp32/sensor_data"  # Définition du sujet MQTT où les données capteurs seront publiées
mqtt_receiver_topic = "iot/esp32/actuator_data"  # Définition du sujet MQTT où les commandes relais seront reçues


def mqtt_callback(topic, msg):
    global last_received_message
    try:
        print("Message reçu sur topic:", topic)
        print("Contenu brut reçu:", msg)
        last_received_message = json_to_micropython(msg)
    except Exception as e:
        print("Erreur callback MQTT:", e)
        last_received_message = None


def micropython_to_json(data):
    try:
        return ujson.dumps(data)
    except Exception as e:
        print("Erreur conversion MicroPython vers JSON:", e)
        return None


def json_to_micropython(json_message):
    try:
        if isinstance(json_message, bytes):
            json_message = json_message.decode("utf-8")
        return ujson.loads(json_message)
    except Exception as e:
        print("Erreur conversion JSON vers MicroPython:", e)
        return None


def connect_wifi(ssid, password):
    try:
        wlan = network.WLAN(network.STA_IF)  # Création de l'interface WLAN en mode station (STA_IF)
        wlan.active(False)  # Désactivation initiale de l'interface Wi-Fi
        time.sleep(1)
        wlan.active(True)  # Réactivation de l'interface Wi-Fi
        time.sleep(1)

        if not wlan.isconnected():  # Vérifie si la connexion Wi-Fi n'est pas encore établie
            wlan.connect(ssid, password)  # Connexion au réseau Wi-Fi
            while not wlan.isconnected():
                time.sleep(0.5)

        print("Wi-Fi OK:", wlan.ifconfig())
        return wlan

    except Exception as e:
        print("Erreur Wi-Fi:", e)
        return None


def connect_mqtt(client_id, broker, receiver_topic):
    try:
        mqtt_client = MQTTClient(client_id, broker)  # Création du client MQTT
        mqtt_client.set_callback(mqtt_callback)  # Définition de la fonction callback pour la réception
        mqtt_client.connect()  # Connexion au broker MQTT
        mqtt_client.subscribe(receiver_topic)  # Abonnement au topic de réception
        print("MQTT OK:", broker)
        print("Abonné au topic:", receiver_topic)
        return mqtt_client

    except Exception as e:
        print("Erreur MQTT:", e)
        return None


def get_dht_value(sensor):
    try:
        sensor.measure()  # Prend une mesure du capteur DHT11
        temperature = sensor.temperature()  # Récupère la température
        humidity = sensor.humidity()  # Récupère l'humidité
        return temperature, humidity

    except Exception as e:
        print("Erreur lecture DHT:", e)
        return None, None


def send_data_mqtt(mqtt_client, mqtt_sender_topic, temperature, humidity):
    try:
        if mqtt_client is None:
            print("Client MQTT non connecté, envoi annulé")
            return

        if temperature is None or humidity is None:
            print("Données invalides, envoi annulé")
            return

        # Crée un message formaté en JSON
        message_dict = {
            "temperature": temperature,
            "humidity": humidity
        }

        message_json = micropython_to_json(message_dict)

        if message_json is None:
            print("Conversion JSON échouée, envoi annulé")
            return

        mqtt_client.publish(mqtt_sender_topic, message_json)  # Publie les données
        print("Données envoyées:", message_json)

    except Exception as e:
        print("Erreur envoi MQTT:", e)


def receive_data_mqtt(mqtt_client, mqtt_receiver_topic):
    global last_received_message
    try:
        if mqtt_client is None:
            print("Client MQTT non connecté, réception annulée")
            return None

        mqtt_client.check_msg()  # Vérifie si un message est reçu sur le topic souscrit : Hey MQTT, est-ce qu’un message est arrivé ? Si oui, appelle le callback

        if last_received_message is not None:
            received_data = last_received_message
            last_received_message = None
            print("Données reçues:", received_data)
            return received_data

        return None

    except Exception as e:
        print("Erreur réception MQTT:", e)
        return None


def manage_relay(relay_value):
    try:
        if relay_value == 1:
            relay_pin.value(1)
            print("Relais activé sur pin 4")
        else:
            relay_pin.value(0)
            print("Relais désactivé sur pin 4")
    except Exception as e:
        print("Erreur gestion relais:", e)


def main():
    wlan = connect_wifi(ssid, password)
    mqtt_client = connect_mqtt(mqtt_client_id, mqtt_broker, mqtt_receiver_topic)

    while True:
        try:
            # Vérification connexion Wi-Fi
            if wlan is None or not wlan.isconnected():
                print("Reconnexion Wi-Fi...")
                wlan = connect_wifi(ssid, password)

            # Vérification connexion MQTT
            if mqtt_client is None:
                print("Reconnexion MQTT...")
                mqtt_client = connect_mqtt(mqtt_client_id, mqtt_broker, mqtt_receiver_topic)

            temperature, humidity = get_dht_value(sensor)
            send_data_mqtt(mqtt_client, mqtt_sender_topic, temperature, humidity)

            received_data = receive_data_mqtt(mqtt_client, mqtt_receiver_topic)

            if received_data is not None and "relay" in received_data:
                manage_relay(received_data["relay"])

            time.sleep(1)

        except Exception as e:
            print("Erreur générale:", e)
            time.sleep(5)


main()
