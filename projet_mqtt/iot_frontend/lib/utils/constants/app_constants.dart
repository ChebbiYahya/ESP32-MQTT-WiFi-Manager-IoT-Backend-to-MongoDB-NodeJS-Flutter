// Regroupe les constantes de configuration utilisees dans tout le projet.
class AppConstants {
  // Adresse IP du broker MQTT.
  static const String mqttServer = '192.168.174.205';
  // Identifiant unique du client Flutter sur le broker.
  static const String mqttClientId = 'flutter_client';
  // Port d'ecoute MQTT.
  static const int mqttPort = 1883;
  // Topic sur lequel les donnees capteurs sont publiees.
  static const String mqttReceiverTopic = 'iot/esp32/sensor_data';
  static const String mqttSenderTopic = 'iot/esp32/actuator_data';

  // Endpoint HTTP reserve a une consultation historique eventuelle.
  static const String historicalUrl = 'http://192.168.174.205:3000/historique';
}
