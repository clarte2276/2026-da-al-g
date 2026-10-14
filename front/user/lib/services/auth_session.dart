import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../data/conversation_store.dart';
import 'ai_api_client.dart';

class AuthSession {
  AuthSession._();

  static const _storageKey = 'auth_session';
  static const _storage = FlutterSecureStorage();

  static final ValueNotifier<AuthResponse?> listenable =
      ValueNotifier<AuthResponse?>(null);

  static AuthResponse? get current => listenable.value;
  static set current(AuthResponse? value) => listenable.value = value;

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
          await _syncData(session.user.id);
        }
      }
    } catch (_) {
      // Corrupt stored session: ignore and fall back to logged out.
    }
  }

  static Future<void> signIn(AuthResponse response) async {
    current = response;
    await _storage.write(
      key: _storageKey,
      value: jsonEncode(response.toJson()),
    );
    await ConversationStore.instance.load(response.user.id);
    await _syncData(response.user.id);
  }

  static Future<void> passwordChanged() async {
    final session = current;
    if (session == null) return;
    final updated = session.copyWith(
      user: session.user.copyWith(mustChangePassword: false),
    );
    current = updated;
    await _storage.write(key: _storageKey, value: jsonEncode(updated.toJson()));
  }

  static void requirePasswordChange() {
    final session = current;
    if (session == null || session.user.mustChangePassword) return;
    final updated = session.copyWith(
      user: session.user.copyWith(mustChangePassword: true),
    );
    current = updated;
    unawaited(
      _storage
          .write(key: _storageKey, value: jsonEncode(updated.toJson()))
          .catchError((Object _) {}),
    );
  }

  static Future<void> _syncData(String userId) async {
    final prefs = await SharedPreferences.getInstance();
    final marker = 'server_data_imported_$userId';
    final client = AiApiClient();
    try {
      if (prefs.getBool(marker) != true) {
        await client.importLocal(
          ConversationStore.instance.conversations
              .map((c) => c.toJson())
              .toList(),
        );
        await prefs.setBool(marker, true);
      }
      await ConversationStore.instance.sync();
    } catch (_) {
      // Keep local data and retry on the next sign-in or app start.
    } finally {
      client.close();
    }
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

String? validatePasswordChange(
  String current,
  String next,
  String confirmation,
) => switch ((current, next, confirmation)) {
  ('', _, _) => '현재 비밀번호를 입력해 주세요.',
  (_, final n, _) when n.length < 8 => '새 비밀번호는 8자 이상이어야 합니다.',
  (_, final n, final c) when n != c => '새 비밀번호가 서로 다릅니다.',
  _ => null,
};
