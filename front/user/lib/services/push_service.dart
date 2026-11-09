import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

import '../screens/exchange_screen.dart';
import 'ai_api_client.dart';

@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  try {
    await Firebase.initializeApp();
  } catch (_) {
    // Firebase config is optional until the app is configured.
  }
}

class PushService {
  PushService._();
  static final instance = PushService._();
  final navigatorKey = GlobalKey<NavigatorState>();

  static const _channel = AndroidNotificationChannel(
    'exchange',
    '교번교체 알림',
    description: '교번교체 게시물 알림',
    importance: Importance.high,
  );
  final _notifications = FlutterLocalNotificationsPlugin();
  StreamSubscription<String>? _tokenSubscription;
  String? _accessToken;
  Map<String, dynamic>? _pendingTap;
  bool _enabled = false;

  Future<void> init() async {
    if (kIsWeb || !Platform.isAndroid) return;
    try {
      await Firebase.initializeApp();
      FirebaseMessaging.onBackgroundMessage(
        _firebaseMessagingBackgroundHandler,
      );
      await _notifications
          .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin
          >()
          ?.createNotificationChannel(_channel);
      FirebaseMessaging.onMessage.listen(_showForeground);
      FirebaseMessaging.onMessageOpenedApp.listen(
        (message) => _handleTap(message.data),
      );
      _enabled = true;
      final initial = await FirebaseMessaging.instance.getInitialMessage();
      if (initial != null) _handleTap(initial.data);
    } catch (_) {
      _enabled = false;
    }
  }

  Future<void> register(String accessToken) async {
    if (!_enabled) return;
    try {
      _accessToken = accessToken;
      await FirebaseMessaging.instance.requestPermission();
      final token = await FirebaseMessaging.instance.getToken();
      if (token != null) await _registerToken(token, accessToken);
      _tokenSubscription ??= FirebaseMessaging.instance.onTokenRefresh.listen((
        token,
      ) {
        final current = _accessToken;
        if (current != null) unawaited(_registerToken(token, current));
      });
    } catch (_) {
      // Push is best-effort; authentication must continue to work.
    }
  }

  Future<void> _registerToken(String token, String accessToken) async {
    final client = AiApiClient();
    try {
      await client.registerPushToken(token, accessToken);
    } catch (_) {
      // Push is best-effort; authentication must continue to work.
    } finally {
      client.close();
    }
  }

  Future<void> unregister(String accessToken) async {
    if (!_enabled) return;
    try {
      final token = await FirebaseMessaging.instance.getToken();
      if (token != null) {
        final client = AiApiClient();
        try {
          await client.unregisterPushToken(token, accessToken);
        } finally {
          client.close();
        }
      }
    } catch (_) {
      // Best-effort cleanup before logging out.
    }
    _accessToken = null;
    await _tokenSubscription?.cancel();
    _tokenSubscription = null;
  }

  Future<void> _showForeground(RemoteMessage message) async {
    final notification = message.notification;
    if (notification == null) return;
    await _notifications.show(
      id: message.hashCode,
      title: notification.title,
      body: notification.body,
      notificationDetails: const NotificationDetails(
        android: AndroidNotificationDetails(
          'exchange',
          '교번교체 알림',
          channelDescription: '교번교체 게시물 알림',
          importance: Importance.high,
          priority: Priority.high,
        ),
      ),
      payload: jsonEncode(message.data),
    );
  }

  void _handleTap(dynamic data) {
    if (data is! Map || data['type'] != 'exchange') return;
    _pendingTap = Map<String, dynamic>.from(data);
    openPendingTap();
  }

  void handleLocalNotificationResponse(NotificationResponse response) {
    final payload = response.payload;
    if (payload != null) _handleTap(jsonDecode(payload));
  }

  void openPendingTap() {
    if (_pendingTap == null) return;
    final navigator = navigatorKey.currentState;
    if (navigator == null) return;
    _pendingTap = null;
    navigator.push(
      MaterialPageRoute<void>(builder: (_) => const ExchangeScreen()),
    );
  }
}
