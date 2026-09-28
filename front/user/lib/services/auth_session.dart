import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../data/conversation_store.dart';
import 'ai_api_client.dart';

class AuthSession {
  AuthSession._();

  static const _storageKey = 'auth_session';
  static const _storage = FlutterSecureStorage();

  static AuthResponse? current;

  static Future<void> restore() async {
    // 예전 버전이 평문으로 남긴 세션은 지운다.
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_storageKey);

    final raw = await _storage.read(key: _storageKey);
    if (raw == null) {
      return;
    }
    try {
      final decoded = jsonDecode(raw);
      if (decoded is Map<String, dynamic>) {
        final session = AuthResponse.fromJson(decoded);
        if (session.isExpired) {
          await _storage.delete(key: _storageKey);
        } else {
          current = session;
          await ConversationStore.instance.load(session.user.id);
        }
      }
    } catch (_) {
      // Corrupt stored session: ignore and fall back to logged out.
    }
  }

  static Future<void> signIn(AuthResponse response) async {
    current = response;
    await _storage.write(key: _storageKey, value: jsonEncode(response.toJson()));
    await ConversationStore.instance.load(response.user.id);
  }

  static Future<void> signOut() async {
    final token = current?.accessToken;
    current = null;
    ConversationStore.instance.clear();
    await _storage.delete(key: _storageKey);
    if (token != null && token.isNotEmpty) {
      final client = AiApiClient();
      // 서버 세션 폐기는 best-effort.
      client.logout(token).catchError((_) {}).whenComplete(client.close);
    }
  }
}
