import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import 'ai_api_client.dart';

class AuthSession {
  AuthSession._();

  static const _storageKey = 'auth_session';

  static AuthResponse? current;

  static Future<void> restore() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_storageKey);
    if (raw == null) {
      return;
    }
    try {
      final decoded = jsonDecode(raw);
      if (decoded is Map<String, dynamic>) {
        final session = AuthResponse.fromJson(decoded);
        if (session.isExpired) {
          await prefs.remove(_storageKey);
        } else {
          current = session;
        }
      }
    } catch (_) {
      // Corrupt stored session: ignore and fall back to logged out.
    }
  }

  static Future<void> signIn(AuthResponse response) async {
    current = response;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_storageKey, jsonEncode(response.toJson()));
  }

  static Future<void> signOut() async {
    final token = current?.accessToken;
    current = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_storageKey);
    if (token != null && token.isNotEmpty) {
      final client = AiApiClient();
      // 서버 세션 폐기는 best-effort.
      client.logout(token).catchError((_) {}).whenComplete(client.close);
    }
  }
}
