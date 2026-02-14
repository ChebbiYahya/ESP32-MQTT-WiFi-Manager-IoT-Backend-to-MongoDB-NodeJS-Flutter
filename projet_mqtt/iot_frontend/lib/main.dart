import 'dart:convert'; // Importation de la bibliothèque pour la gestion des données JSON

import 'package:flutter/material.dart'; // Importation de la bibliothèque Flutter pour les composants d'interface utilisateur
import 'package:http/http.dart'
    as http; // Importation de la bibliothèque HTTP pour faire des requêtes réseau
import 'package:mqtt_client/mqtt_client.dart'
    as mqtt; // Importation de la bibliothèque MQTT pour la communication avec les dispositifs IoT
import 'package:mqtt_client/mqtt_server_client.dart'; // Importation de la classe pour gérer la connexion au serveur MQTT

void main() {
  runApp(MyApp()); // Lancement de l'application Flutter
}

class MyApp extends StatelessWidget {
  // Classe principale de l'application
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: SensorDataScreen(),
    ); // Affichage de l'écran de données du capteur
  }
}

class SensorDataScreen extends StatefulWidget {
  // Ecran principal qui gère l'affichage des données des capteurs
  @override
  _SensorDataScreenState createState() => _SensorDataScreenState(); // Création de l'état de l'écran
}

class _SensorDataScreenState extends State<SensorDataScreen> {
  MqttServerClient? client; // Déclaration d'une variable pour le client MQTT
  String temperature =
      "Loading..."; // Variable pour stocker la température (initialisée à "Loading...")
  String humidity =
      "Loading..."; // Variable pour stocker l'humidité (initialisée à "Loading...")

  @override
  void initState() {
    super.initState(); // Initialisation de l'état
    _connectMQTT(); // Connexion au serveur MQTT
    _fetchHistoricalData(); // Récupération des données historiques depuis le serveur
  }

  void _connectMQTT() async {
    // Méthode pour se connecter au serveur MQTT
    client = MqttServerClient(
      '192.168.100.9',
      'flutter_client',
    ); // Définition de l'adresse du serveur et du nom du client
    client!.port = 1883; // Définition du port MQTT (par défaut, c'est 1883)
    client!.keepAlivePeriod =
        20; // Définition de la durée de vie de la connexion (en secondes)
    client!.logging(on: false); // Désactivation des logs
    client!.onDisconnected =
        _onDisconnected; // Définition du callback en cas de déconnexion

    final connMess =
        mqtt.MqttConnectMessage() // Création du message de connexion MQTT
            .withClientIdentifier(
              'flutter_client',
            ) // Définition de l'identifiant du client
            .withWillQos(
              mqtt.MqttQos.atMostOnce,
            ); // Définition de la qualité de service
    client!.connectionMessage =
        connMess; // Affectation du message de connexion au client

    try {
      await client!.connect(); // Tentative de connexion au serveur MQTT
    } catch (e) {
      print(
        'MQTT connection failed: $e',
      ); // Affichage d'un message d'erreur en cas d'échec de la connexion
      client!.disconnect(); // Déconnexion du client en cas d'erreur
      return;
    }

    if (client!.connectionStatus?.state != mqtt.MqttConnectionState.connected) {
      // Vérification si la connexion est réussie
      print(
        'MQTT not connected: ${client!.connectionStatus}',
      ); // Affichage du statut de la connexion
      client!.disconnect(); // Déconnexion en cas de problème
      return;
    }

    client!.subscribe(
      'iot/esp32/sensor_data',
      mqtt.MqttQos.atMostOnce,
    ); // Abonnement au sujet MQTT pour recevoir les données des capteurs

    client!.updates!.listen((
      // Écoute des mises à jour des messages MQTT
      List<mqtt.MqttReceivedMessage<mqtt.MqttMessage>>
      event, // Récupération des messages reçus
    ) {
      final mqtt.MqttPublishMessage recMessage =
          event[0].payload
              as mqtt.MqttPublishMessage; // Extraction du message reçu
      final payload = mqtt.MqttPublishPayload.bytesToStringAsString(
        recMessage
            .payload
            .message, // Conversion du message en chaîne de caractères
      );
      final data = jsonDecode(payload); // Décodage du JSON du message
      setState(() {
        // Mise à jour de l'état pour afficher les nouvelles données
        temperature =
            data['temperature'].toString(); // Mise à jour de la température
        humidity = data['humidity'].toString(); // Mise à jour de l'humidité
      });
    });
  }

  void _onDisconnected() {
    // Callback en cas de déconnexion du client MQTT
    print('MQTT disconnected'); // Affichage d'un message en cas de déconnexion
  }

  Future<void> _fetchHistoricalData() async {
    // Méthode pour récupérer les données historiques
    final response = await http.get(
      Uri.parse(
        'http://192.168.100.9:3000/historique',
      ), // Envoi d'une requête HTTP pour récupérer les données historiques
    );
    if (response.statusCode == 200) {
      // Vérification du statut de la réponse
      print(
        'Historical data: ${response.body}',
      ); // Affichage des données historiques
    } else {
      print(
        'Failed to load historical data',
      ); // Message d'erreur en cas d'échec de la requête
    }
  }

  @override
  Widget build(BuildContext context) {
    // Méthode pour construire l'interface utilisateur
    return Scaffold(
      // Structure de l'écran
      appBar: AppBar(
        title: Text("IoT Sensor Data"),
      ), // Barre d'applications avec le titre
      body: Center(
        // Contenu de l'écran centré
        child: Column(
          // Colonne contenant les éléments à afficher
          mainAxisAlignment:
              MainAxisAlignment.center, // Centrage vertical des éléments
          children: <Widget>[
            // Liste des éléments
            Row(
              // Première ligne pour afficher la température
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(
                  Icons.thermostat,
                  size: 24,
                  color: Colors.redAccent,
                ), // Icône de température
                const SizedBox(width: 8), // Espace entre l'icône et le texte
                Text(
                  'Temperature: $temperature °C', // Affichage de la température
                  style: TextStyle(fontSize: 24),
                ),
              ],
            ),
            const SizedBox(height: 8), // Espacement vertical
            Row(
              // Deuxième ligne pour afficher l'humidité
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(
                  Icons.water_drop,
                  size: 24,
                  color: Colors.blueAccent,
                ), // Icône d'humidité
                const SizedBox(width: 8), // Espace entre l'icône et le texte
                Text(
                  'Humidity: $humidity%',
                  style: TextStyle(fontSize: 24),
                ), // Affichage de l'humidité
              ],
            ),
          ],
        ),
      ),
    );
  }
}
