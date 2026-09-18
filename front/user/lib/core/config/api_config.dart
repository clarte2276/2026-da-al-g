import 'package:flutter/foundation.dart';

String defaultApiBaseUrl() {
  const configured = String.fromEnvironment('API_BASE_URL');
  if (configured.trim().isNotEmpty) {
    return configured.trim().replaceAll(RegExp(r'/+$'), '');
  }
  if (kIsWeb) {
    return 'http://localhost:8000';
  }
  if (defaultTargetPlatform == TargetPlatform.android) {
    return 'http://10.0.2.2:8000';
  }
  return 'http://localhost:8000';
}
