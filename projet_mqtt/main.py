import dht  # Importation du module dht pour gérer les capteurs DHT (DHT11 ou DHT22) pour la mesure de température et d'humidité
import machine  # Importation du module machine pour interagir avec le matériel (GPIO)
import time  # Importation du module time pour gérer les temporisations (attentes)
import ubinascii  # Importation du module ubinascii pour manipuler les données binaires (par exemple, pour l'encodage en base64)
import network  # Importation du module network pour gérer les connexions réseau
from umqtt.simple import MQTTClient  # Importation du module MQTTClient pour la communication avec un broker MQTT

# Configuration du GPIO pour le capteur DHT11
sensor = dht.DHT11(machine.Pin(13))

# Connexion Wi-Fi (remplacez par vos identifiants)
ssid = "Chebbi_WiFi"  # Définition du nom du réseau Wi-Fi auquel se connecter
password = "chebbi123"  # Définition du mot de passe du réseau Wi-Fi

# Configuration du client MQTT
mqtt_broker = "192.168.100.9"  # Définition de l'adresse IP du broker MQTT (le serveur auquel se connecter pour échanger les messages)
mqtt_client_id = ubinascii.b2a_base64(machine.unique_id()).strip()  # Génère un ID unique pour le client MQTT à partir de l'ID unique de la machine, encodé en base64
mqtt_topic = "iot/esp32/sensor_data"  # Définition du sujet (topic) MQTT où les données seront publiées


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


def connect_mqtt(client_id, broker):
    try:
        mqtt_client = MQTTClient(client_id, broker)  # Création du client MQTT
        mqtt_client.connect()  # Connexion au broker MQTT
        print("MQTT OK:", broker)
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


def send_data_mqtt(mqtt_client, mqtt_topic, temperature, humidity):
    try:
        if temperature is None or humidity is None:
            print("Données invalides, envoi annulé")
            return

        # Crée un message formaté en JSON
        message = "{ \"temperature\": " + str(temperature) + ", \"humidity\": " + str(humidity) + " }"

        mqtt_client.publish(mqtt_topic, message)  # Publie les données
        print("Données envoyées:", message)

    except Exception as e:
        print("Erreur envoi MQTT:", e)


def main():
    wlan = connect_wifi(ssid, password)
    mqtt_client = connect_mqtt(mqtt_client_id, mqtt_broker)

    while True:
        try:
            # Vérification connexion Wi-Fi
            if wlan is None or not wlan.isconnected():
                print("Reconnexion Wi-Fi...")
                wlan = connect_wifi(ssid, password)

            # Vérification connexion MQTT
            if mqtt_client is None:
                print("Reconnexion MQTT...")
                mqtt_client = connect_mqtt(mqtt_client_id, mqtt_broker)

            temperature, humidity = get_dht_value(sensor)
            send_data_mqtt(mqtt_client, mqtt_topic, temperature, humidity)

            time.sleep(10)

        except Exception as e:
            print("Erreur générale:", e)
            time.sleep(5)


main()