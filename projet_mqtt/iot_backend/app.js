// Importation des modules nécessaires
const express = require('express'); // Importation du framework Express pour créer le serveur web
const mqtt = require('mqtt'); // Importation de la bibliothèque MQTT pour la communication via le protocole MQTT
const mongoose = require('mongoose'); // Importation de Mongoose pour interagir avec MongoDB
const bodyParser = require('body-parser'); // Importation du middleware pour analyser le corps des requêtes HTTP (JSON)

// Configurer la connexion au serveur MongoDB
mongoose.connect('mongodb://localhost:27017/iot'); // Connexion à la base de données MongoDB (nommée "iot")
const db = mongoose.connection; // Référence à la connexion MongoDB

// Gestion des erreurs de connexion MongoDB
db.on('error', console.error.bind(console, 'connection error:')); // Affiche une erreur en cas de problème de connexion
db.once('open', () => { // Une fois la connexion établie, afficher un message de succès
  console.log('Connecté à MongoDB');
});

// Définition du modèle de données pour stocker les informations des capteurs
const SensorData = mongoose.model('SensorData', {  // Définition du modèle "SensorData"
  temperature: Number, // Température du capteur (de type numérique)
  humidity: Number, // Humidité du capteur (de type numérique)
  timestamp: { type: Date, default: Date.now } // Timestamp de la lecture (par défaut, l'heure actuelle)
});

// Initialisation de l'application Express
const app = express();
app.use(bodyParser.json()); // Utilisation de body-parser pour analyser les requêtes JSON entrantes

// Connexion au broker MQTT
const client = mqtt.connect('mqtt://192.168.100.9'); // Connexion au broker MQTT à l'adresse spécifiée (remplacer par votre propre broker)

client.on('connect', () => {  // Lorsque la connexion au broker MQTT est réussie
  console.log('Connecté au broker MQTT'); // Afficher un message de succès
  client.subscribe('iot/esp32/sensor_data');  // S'abonner au sujet MQTT 'iot/esp32/sensor_data' pour recevoir les données des capteurs
});

client.on('message', async (topic, message) => {  // Lorsque un message est reçu sur le sujet abonné
  console.log('Message reçu:', message.toString()); // Afficher le message reçu

  const data = JSON.parse(message.toString()); // Parser le message reçu en objet JSON

  // Si la température est supérieure à 25, enregistrer les données dans MongoDB
  if (data.temperature > 25) {
    const newData = new SensorData({  // Créer une nouvelle instance du modèle "SensorData"
      temperature: data.temperature,  // Assigner la température reçue
      humidity: data.humidity        // Assigner l'humidité reçue
    });

    try {
      const savedData = await newData.save();  // Sauvegarder les données dans MongoDB
      console.log('Données enregistrées dans l\'historique:', savedData);  // Afficher un message si l'enregistrement est réussi
    } catch (err) {
      console.error('Erreur lors de l\'enregistrement des données:', err);  // Afficher une erreur en cas de problème d'enregistrement
    }
  }
});

// Définir une API pour récupérer les données historiques des capteurs
app.get('/historique', async (req, res) => {  // Endpoint HTTP pour obtenir l'historique des données
  try {
    const data = await SensorData.find({});  // Récupérer toutes les données de la collection "SensorData"
    res.json(data);  // Retourner les données sous forme de réponse JSON
  } catch (err) {
    res.status(500).send('Erreur lors de la récupération des données');  // En cas d'erreur, retourner un message d'erreur avec le code 500
  }
});

// Exporter l'application Express pour utilisation dans un autre fichier
module.exports = app;