import 'dart:async';
import 'dart:convert';

import 'package:get/get.dart';
import 'package:iot_frontend/models/sensor_data_model.dart';
import 'package:mqtt_client/mqtt_client.dart' as mqtt;
import 'package:mqtt_client/mqtt_server_client.dart';

import '../utils/constants/app_constants.dart';

// Controleur GetX responsable de la connexion MQTT et des donnees affichees.
class SensorController extends GetxController {
  // Raccourci pratique pour recuperer l'instance deja injectee dans GetX.
  static SensorController get instance => Get.find();

  // Client MQTT utilise pour se connecter au broker et publier/souscrire aux topics.
  MqttServerClient? client;

  /// Etats observables lies aux donnees capteurs, au relais et a la connexion.
  final RxString temperature = 'Loading...'.obs;
  final RxString humidity = 'Loading...'.obs;
  final RxBool relayEnabled = false.obs;
  final RxBool isConnected = false.obs;
  final RxString errorMessage = ''.obs;

  // Conserve l'abonnement au flux MQTT pour pouvoir le fermer proprement.
  StreamSubscription? _mqttSubscription;

  @override
  void onInit() {
    super.onInit();
    // Lance automatiquement la connexion MQTT au demarrage du controller.
    connectMQTT();
  }

  Future<void> connectMQTT() async {
    try {
      // Prepare l'objet client avec tous les parametres necessaires.
      configureClient();

      // Demande la connexion au broker MQTT.
      await client!.connect();

      // Si la connexion n'est pas etablie, on sort proprement.
      if (!isClientConnected()) {
        errorMessage.value =
            'MQTT non connecte: ${client!.connectionStatus?.state}';
        client!.disconnect();
        return;
      }

      // Connexion reussie: on met a jour l'etat puis on active la reception.
      isConnected.value = true;
      errorMessage.value = '';
      subscribeToSensorData();
    } catch (e) {
      // Toute erreur de connexion ou de configuration arrive ici.
      errorMessage.value = 'MQTT connection failed: $e';
      isConnected.value = false;
      client?.disconnect();
    }
  }

  void configureClient() {
    // Cree le client MQTT en utilisant l'adresse du broker et l'identifiant Flutter.
    client = MqttServerClient(
      AppConstants.mqttServer,
      AppConstants.mqttClientId,
    );

    // Parametres de base de la connexion MQTT.
    client!.port = AppConstants.mqttPort;
    client!.keepAlivePeriod = 20;
    client!.logging(on: false);
    client!.onDisconnected = onDisconnected;

    // Message/env de connexion transmis au broker lors du connect().
    client!.connectionMessage = mqtt.MqttConnectMessage()
        .withClientIdentifier(AppConstants.mqttClientId)
        .withWillQos(mqtt.MqttQos.atMostOnce);
  }

  bool isClientConnected() {
    // Retourne true seulement si le broker confirme une connexion active.
    return client?.connectionStatus?.state == mqtt.MqttConnectionState.connected;
  }

  void subscribeToSensorData() {
    // Souscrit au topic des donnees capteurs publiees par l'ESP32.
    client?.subscribe(AppConstants.mqttReceiverTopic, mqtt.MqttQos.atMostOnce);

    // Ecoute en continu les messages entrants recus sur les topics souscrits.
    _mqttSubscription = client?.updates?.listen(handleSensorMessage);
  }

  void handleSensorMessage(
    List<mqtt.MqttReceivedMessage<mqtt.MqttMessage?>>? event,
  ) {
    // Protection simple: on ignore les evenements vides ou nuls.
    if (event == null || event.isEmpty) {
      return;
    }

    try {
      // Recupere le message MQTT brut recu depuis le broker.
      final recMessage = event[0].payload as mqtt.MqttPublishMessage;

      // Convertit le payload binaire en texte JSON lisible.
      final payload = mqtt.MqttPublishPayload.bytesToStringAsString(
        recMessage.payload.message,
      );

      // Decode le JSON et construit l'objet metier des donnees capteurs.
      final data = jsonDecode(payload) as Map<String, dynamic>;
      final sensorData = SensorDataModel.fromJson(data);

      // Met a jour les valeurs observees automatiquement par l'interface.
      temperature.value = sensorData.temperature.toString();
      humidity.value = sensorData.humidity.toString();
    } catch (e) {
      // Si le JSON recu est invalide ou inattendu, on remonte l'erreur.
      errorMessage.value = 'Erreur parsing MQTT: $e';
    }
  }

  void onDisconnected() {
    // Synchronise l'etat local lorsque la connexion MQTT tombe.
    isConnected.value = false;
    errorMessage.value = 'MQTT disconnected';
    print('MQTT disconnected');
  }

  Future<void> reconnectMQTT() async {
    // Ferme proprement la session actuelle avant de lancer une nouvelle connexion.
    await disconnectMQTT();
    await connectMQTT();
  }

  Future<void> publishRelayState(bool isEnabled) async {
    // On bloque la publication si le client n'est pas pret ou deconnecte.
    if (client == null || !isConnected.value || !isClientConnected()) {
      errorMessage.value = 'MQTT non connecte';
      return;
    }

    try {
      // Construit le JSON attendu par l'ESP32: {"relay":1} ou {"relay":0}.
      final payload = jsonEncode({'relay': isEnabled ? 1 : 0});

      // Le payload builder transforme la chaine JSON en message MQTT publiable.
      final builder = mqtt.MqttClientPayloadBuilder();
      builder.addString(payload);

      // Envoie l'etat du relais sur le topic dedie aux actionneurs.
      client!.publishMessage(
        AppConstants.mqttSenderTopic,
        mqtt.MqttQos.atMostOnce,
        builder.payload!,
      );

      // Si la publication reussit, on synchronise l'etat local du switch.
      relayEnabled.value = isEnabled;
      errorMessage.value = '';
    } catch (e) {
      // Capture les erreurs de publication MQTT.
      errorMessage.value = 'Erreur publication MQTT: $e';
    }
  }

  Future<void> disconnectMQTT() async {
    // Arrete l'ecoute des messages puis ferme la connexion au broker.
    await _mqttSubscription?.cancel();
    client?.disconnect();
    isConnected.value = false;
  }

  @override
  void onClose() {
    // Nettoyage final quand le controller est detruit par Flutter/GetX.
    _mqttSubscription?.cancel();
    client?.disconnect();
    super.onClose();
  }
}
