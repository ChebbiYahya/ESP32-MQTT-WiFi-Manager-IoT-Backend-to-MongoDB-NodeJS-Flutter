import 'package:flutter/material.dart';
import 'package:get/get.dart';

import 'views/sensor_data_screen.dart';

// Point d'entree de l'application Flutter.
void main() {
  runApp(const MyApp());
}

// Widget racine qui configure GetX et charge l'ecran principal.
class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const GetMaterialApp(
      debugShowCheckedModeBanner: false,
      home: SensorDataScreen(),
    );
  }
}
