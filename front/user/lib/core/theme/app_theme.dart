import 'package:flutter/material.dart';

ThemeData buildAppTheme() {
  final colorScheme = ColorScheme.fromSeed(
    seedColor: const Color(0xFF315CEB),
    brightness: Brightness.light,
  );
  return ThemeData(
    colorScheme: colorScheme,
    useMaterial3: true,
    scaffoldBackgroundColor: const Color(0xFFF7F8FC),
    inputDecorationTheme: const InputDecorationTheme(
      border: InputBorder.none,
      filled: true,
      fillColor: Colors.white,
    ),
  );
}
