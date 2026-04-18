import 'dart:async';
import 'dart:convert';

import 'package:get/get.dart';
import 'package:iot_frontend/models/sensor_data_model.dart';
import 'package:mqtt_client/mqtt_server_client.dart';
import '../utils/constants/app_constants.dart';
import 'package:mqtt_client/mqtt_client.dart' as mqtt;

// Controleur GetX responsable de la connexion MQTT et des donnees affichees.
class SensorController extends GetxController {
  // Raccourci pratique pour recuperer l'instance deja injectee dans GetX.
  static SensorController get instance => Get.find();

  // Client MQTT utilise pour se connecter au broker.
  MqttServerClient? client;

  /// Etat observable qui declenche automatiquement la mise a jour de l'UI.
  final RxString temperature = 'Loading...'.obs;
  final RxString humidity = 'Loading...'.obs;
  final RxBool isConnected = false.obs;
  final RxString errorMessage = ''.obs;

  // Conserve l'abonnement au flux MQTT pour pouvoir le fermer proprement.
  StreamSubscription? _mqttSubscription;

  @override
  void onInit() {
    super.onInit();
    // Lance la connexion des l'initialisation du controleur.
    connectMQTT();
  }

  Future<void> connectMQTT() async {
    try {
      // Cree le client avec l'adresse du broker et l'identifiant de l'application.
      client = MqttServerClient(
        AppConstants.mqttServer, // - l'adresse du broker (serveur MQTT)
        AppConstants
            .mqttClientId, // - un identifiant unique pour cette application (clientId)
      );

      // Configure les parametres de base de la session MQTT.
      client!.port = AppConstants
          .mqttPort; // Configuration du port de communication MQTT (souvent 1883)
      client!.keepAlivePeriod =
          20; // Définition du keepAlive (intervalle en secondes pour maintenir la connexion active)
      client!.logging(
        on: false,
      ); // Activation/désactivation des logs internes du client MQTT
      client!.onDisconnected =
          onDisconnected; // Callback appelée automatiquement lorsque la connexion est interrompue

      // Prepare le message de connexion envoye au broker.
      final connMess = mqtt.MqttConnectMessage()
          .withClientIdentifier(
            AppConstants.mqttClientId,
          ) // Identifiant du client envoyé au broker
          .withWillQos(
            mqtt.MqttQos.atMostOnce,
          ); // QoS du message "Last Will" (message envoyé si le client crash)

      client!.connectionMessage =
          connMess; // Affectation du message de connexion au client MQTT

      // Tente d'etablir la connexion reseau avec le broker MQTT.
      await client!.connect();

      // Verifie que la connexion est bien active avant de s'abonner au topic.
      if (client!.connectionStatus?.state !=
          mqtt.MqttConnectionState.connected) {
        errorMessage.value =
            'MQTT non connectÃ©: ${client!.connectionStatus?.state}';
        client!.disconnect();
        return;
      }

      isConnected.value =
          true; // Si la connexion est réussie → on met à jour l'état
      errorMessage.value = ''; // Réinitialisation du message d'erreur

      // Souscription au topic MQTT où l'ESP32 envoie les données capteurs
      client!.subscribe(AppConstants.mqttTopic, mqtt.MqttQos.atMostOnce);

      // Traite chaque message entrant recu depuis le broker.
      _mqttSubscription = client!.updates!.listen((event) {
        try {
          // Extrait le message MQTT brut depuis l'evenement.
          final mqtt.MqttPublishMessage recMessage =
              event[0].payload as mqtt.MqttPublishMessage;

          // Convertit les octets du payload en chaine JSON lisible.
          final payload = mqtt.MqttPublishPayload.bytesToStringAsString(
            recMessage.payload.message,
          );

          // Transforme le JSON en objet Dart exploitable par l'application.
          final data = jsonDecode(payload) as Map<String, dynamic>;
          final sensorData = SensorDataModel.fromJson(data);

          // Met a jour les valeurs reactives observees par l'interface.
          temperature.value = sensorData.temperature.toString();
          humidity.value = sensorData.humidity.toString();
        } catch (e) {
          errorMessage.value = 'Erreur parsing MQTT: $e';
        }
      });
    } catch (e) {
      // Capture les erreurs de connexion ou de configuration MQTT.
      errorMessage.value = 'MQTT connection failed: $e';
      isConnected.value = false;
      client?.disconnect();
    }
  }

  void onDisconnected() {
    // Maintient l'etat local coherent si le broker coupe la connexion.
    isConnected.value = false;
    errorMessage.value = 'MQTT disconnected';
    print('MQTT disconnected');
  }

  Future<void> reconnectMQTT() async {
    // Repart proprement d'une session vide avant de se reconnecter.
    await disconnectMQTT();
    await connectMQTT();
  }

  Future<void> disconnectMQTT() async {
    // Annule l'ecoute du flux puis ferme la connexion MQTT.
    await _mqttSubscription?.cancel();
    client?.disconnect();
    isConnected.value = false;
  }

  @override
  void onClose() {
    // Libere les ressources quand le controleur est detruit.
    _mqttSubscription?.cancel();
    client?.disconnect();
    super.onClose();
  }
}
