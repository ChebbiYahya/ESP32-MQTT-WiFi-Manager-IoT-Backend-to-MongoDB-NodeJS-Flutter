// Modele metier qui represente une mesure recue depuis le capteur.
class SensorDataModel {
  final double temperature;
  final double humidity;

  SensorDataModel({required this.temperature, required this.humidity});

  // Construit une instance a partir d'un objet JSON.
  factory SensorDataModel.fromJson(Map<String, dynamic> json) {
    return SensorDataModel(
      temperature: (json['temperature'] ?? 0).toDouble(),
      humidity: (json['humidity'] ?? 0).toDouble(),
    );
  }

  // Convertit l'instance en JSON pour un stockage ou un envoi futur.
  Map<String, dynamic> toJson() {
    return {'temperature': temperature, 'humidity': humidity};
  }
}
