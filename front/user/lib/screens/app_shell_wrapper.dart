import 'package:flutter/material.dart';
import '../app_shell.dart';

// Thin wrapper so LoginScreen can reference AppShell without a circular import.
class AppShellWrapper extends StatelessWidget {
  const AppShellWrapper({super.key});

  @override
  Widget build(BuildContext context) => const AppShell();
}
