# Programme MicroPython pour ESP32 :
# - lire la température et l'humidité avec un capteur DHT11 ;
# - publier ces mesures sur un broker MQTT ;
# - recevoir une commande MQTT pour piloter un relais.

import dht  # Module du capteur DHT11/DHT22.
import machine  # Module MicroPython pour accéder au matériel : GPIO, identifiant carte, etc.
import time  # Module utilisé pour les pauses entre les mesures et les reconnexions.
import ubinascii  # Module utilisé ici pour convertir l'identifiant matériel en texte.
import network  # Module de gestion du Wi-Fi.
import ujson  # Module JSON optimisé pour MicroPython.
from umqtt.simple import MQTTClient  # Client MQTT léger adapté à MicroPython.

# Le capteur DHT11 est branché sur le GPIO 4 de l'ESP32.
sensor = dht.DHT11(machine.Pin(4))

# Le relais est branché sur le GPIO 2 et configuré en sortie.
relay_pin = machine.Pin(2, machine.Pin.OUT)
relay_pin.value(0)  # Au démarrage, le relais est désactivé.

# Cette variable sert de tampon entre la fonction callback MQTT et la boucle principale.
# Quand un message arrive, la callback le décode et le stocke ici.
last_received_message = None

# Identifiants du réseau Wi-Fi auquel l'ESP32 doit se connecter.
ssid = "null"
password = "yahya123"

# Paramètres MQTT.
mqtt_broker = "192.168.174.205"  # Adresse IP du broker MQTT.
mqtt_client_id = ubinascii.b2a_base64(machine.unique_id()).strip()  # Identifiant unique du client ESP32.
mqtt_sender_topic = "iot/esp32/sensor_data"  # Topic utilisé pour publier les mesures du capteur.
mqtt_receiver_topic = "iot/esp32/actuator_data"  # Topic utilisé pour recevoir les commandes du relais.


def mqtt_callback(topic, msg):
    # Cette fonction est appelée automatiquement par le client MQTT
    # lorsqu'un message arrive sur un topic auquel l'ESP32 est abonné.
    global last_received_message
    try:
        print("Message reçu sur topic:", topic)
        print("Contenu brut reçu:", msg)
        # Le message reçu par MQTT est au format JSON.
        # On le convertit en objet Python/MicroPython pour pouvoir lire ses champs.
        last_received_message = json_to_micropython(msg)
    except Exception as e:
        print("Erreur callback MQTT:", e)
        last_received_message = None


def micropython_to_json(data):
    # Convertit un dictionnaire MicroPython en chaîne JSON avant l'envoi MQTT.
    try:
        return ujson.dumps(data)
    except Exception as e:
        print("Erreur conversion MicroPython vers JSON:", e)
        return None


def json_to_micropython(json_message):
    # Convertit un message JSON reçu par MQTT en dictionnaire MicroPython.
    try:
        # Les messages MQTT arrivent souvent en bytes.
        # ujson.loads attend une chaîne de caractères, donc on décode si nécessaire.
        if isinstance(json_message, bytes):
            json_message = json_message.decode("utf-8")
        return ujson.loads(json_message)
    except Exception as e:
        print("Erreur conversion JSON vers MicroPython:", e)
        return None


def connect_wifi(ssid, password):
    # Établit la connexion Wi-Fi et retourne l'interface WLAN.
    # En cas d'échec, retourne None pour permettre une tentative de reconnexion plus tard.
    try:
        wlan = network.WLAN(network.STA_IF)  # Mode station : l'ESP32 se connecte à un point d'accès.
        wlan.active(False)  # Réinitialisation de l'interface Wi-Fi.
        time.sleep(1)
        wlan.active(True)  # Activation de l'interface Wi-Fi.
        time.sleep(1)

        if not wlan.isconnected():
            wlan.connect(ssid, password)

            # La boucle attend que l'ESP32 obtienne une connexion réseau.
            while not wlan.isconnected():
                time.sleep(0.5)

        print("Wi-Fi OK:", wlan.ifconfig())
        return wlan

    except Exception as e:
        print("Erreur Wi-Fi:", e)
        return None


def connect_mqtt(client_id, broker, receiver_topic):
    # Crée le client MQTT, le connecte au broker, puis l'abonne au topic de commande.
    try:
        mqtt_client = MQTTClient(client_id, broker)
        mqtt_client.set_callback(mqtt_callback)  # Associe la callback appelée à chaque message reçu.
        mqtt_client.connect()
        mqtt_client.subscribe(receiver_topic)
        print("MQTT OK:", broker)
        print("Abonné au topic:", receiver_topic)
        return mqtt_client

    except Exception as e:
        print("Erreur MQTT:", e)
        return None


def get_dht_value(sensor):
    # Lit les valeurs du capteur DHT11.
    # Retourne un tuple (temperature, humidity).
    try:
        sensor.measure()  # Lance une nouvelle mesure.
        temperature = sensor.temperature()  # Température en degrés Celsius.
        humidity = sensor.humidity()  # Humidité relative en pourcentage.
        return temperature, humidity

    except Exception as e:
        print("Erreur lecture DHT:", e)
        return None, None


def send_data_mqtt(mqtt_client, mqtt_sender_topic, temperature, humidity):
    # Prépare les mesures au format JSON et les publie sur le topic MQTT des capteurs.
    try:
        if mqtt_client is None:
            print("Client MQTT non connecté, envoi annulé")
            return

        # Si la lecture du capteur a échoué, on n'envoie pas de données incorrectes.
        if temperature is None or humidity is None:
            print("Données invalides, envoi annulé")
            return

        # Dictionnaire qui représente le message à envoyer.
        message_dict = {
            "temperature": temperature,
            "humidity": humidity
        }

        # Conversion du dictionnaire en chaîne JSON compréhensible par les autres applications.
        message_json = micropython_to_json(message_dict)

        if message_json is None:
            print("Conversion JSON échouée, envoi annulé")
            return

        mqtt_client.publish(mqtt_sender_topic, message_json)
        print("Données envoyées:", message_json)

    except Exception as e:
        print("Erreur envoi MQTT:", e)


def receive_data_mqtt(mqtt_client, mqtt_receiver_topic):
    # Vérifie si une commande MQTT a été reçue.
    # Si oui, retourne le dictionnaire décodé. Sinon, retourne None.
    global last_received_message
    try:
        if mqtt_client is None:
            print("Client MQTT non connecté, réception annulée")
            return None

        # check_msg ne bloque pas le programme :
        # il vérifie rapidement s'il y a un message en attente.
        # Si un message existe, mqtt_callback est appelée automatiquement.
        mqtt_client.check_msg()

        if last_received_message is not None:
            # On copie le message reçu puis on vide le tampon pour ne pas le traiter deux fois.
            received_data = last_received_message
            last_received_message = None
            print("Données reçues:", received_data)
            return received_data

        return None

    except Exception as e:
        print("Erreur réception MQTT:", e)
        return None


def manage_relay(relay_value):
    # Pilote le relais selon la valeur reçue :
    # 1 active le relais, toute autre valeur le désactive.
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
    # Première tentative de connexion au Wi-Fi et au broker MQTT.
    wlan = connect_wifi(ssid, password)
    mqtt_client = connect_mqtt(mqtt_client_id, mqtt_broker, mqtt_receiver_topic)

    # Boucle infinie principale du programme embarqué.
    while True:
        try:
            # Si le Wi-Fi est perdu, on tente de le rétablir.
            if wlan is None or not wlan.isconnected():
                print("Reconnexion Wi-Fi...")
                wlan = connect_wifi(ssid, password)

            # Si le client MQTT n'existe pas, on tente de se reconnecter au broker.
            if mqtt_client is None:
                print("Reconnexion MQTT...")
                mqtt_client = connect_mqtt(mqtt_client_id, mqtt_broker, mqtt_receiver_topic)

            # Lecture du capteur puis publication des mesures.
            temperature, humidity = get_dht_value(sensor)
            send_data_mqtt(mqtt_client, mqtt_sender_topic, temperature, humidity)

            # Réception éventuelle d'une commande, par exemple {"relay": 1}.
            received_data = receive_data_mqtt(mqtt_client, mqtt_receiver_topic)

            if received_data is not None and "relay" in received_data:
                manage_relay(received_data["relay"])

            # Pause d'une seconde pour éviter d'envoyer trop de messages MQTT.
            time.sleep(1)

        except Exception as e:
            # Sécurité générale : en cas d'erreur inattendue, on affiche l'erreur
            # et on attend avant de recommencer la boucle.
            print("Erreur générale:", e)
            time.sleep(5)


# Point d'entrée du programme : lance la boucle principale.
main()
