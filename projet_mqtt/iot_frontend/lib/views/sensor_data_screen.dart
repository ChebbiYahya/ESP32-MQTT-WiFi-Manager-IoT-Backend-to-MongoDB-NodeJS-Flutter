import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../controllers/sensor_controller.dart';

// Ecran principal qui affiche les mesures recues en temps reel.
class SensorDataScreen extends StatefulWidget {
  const SensorDataScreen({super.key});

  @override
  State<SensorDataScreen> createState() => _SensorDataScreenState();
}

class _SensorDataScreenState extends State<SensorDataScreen> {
  // Enregistre et recupere le controleur qui pilote l'etat de l'ecran.
  final SensorController controller = Get.put(SensorController());

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("IoT Sensor Data"),
        actions: [
          Obx(() {
            // L'icone wifi change automatiquement selon l'etat de connexion.
            return Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Icon(
                controller.isConnected.value ? Icons.wifi : Icons.wifi_off,
                color: controller.isConnected.value ? Colors.green : Colors.red,
              ),
            );
          }),
        ],
      ),
      body: Center(
        child: Obx(() {
          // Le contenu se reconstruit a chaque changement des variables observees.
          return Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              // Affiche les erreurs de connexion ou de traitement MQTT.
              if (controller.errorMessage.value.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Text(
                    controller.errorMessage.value,
                    style: const TextStyle(color: Colors.red),
                    textAlign: TextAlign.center,
                  ),
                ),

              // Ligne dediee a l'affichage de la temperature courante.
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(
                    Icons.thermostat,
                    size: 24,
                    color: Colors.redAccent,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Temperature: ${controller.temperature.value} °C',
                    style: const TextStyle(fontSize: 24),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              // Ligne dediee a l'affichage de l'humidite courante.
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(
                    Icons.water_drop,
                    size: 24,
                    color: Colors.blueAccent,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Humidity: ${controller.humidity.value}%',
                    style: const TextStyle(fontSize: 24),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Permet de relancer manuellement la connexion MQTT.
              ElevatedButton.icon(
                onPressed: controller.reconnectMQTT,
                icon: const Icon(Icons.refresh),
                label: const Text("Reconnect MQTT"),
              ),
            ],
          );
        }),
      ),
    );
  }
}
