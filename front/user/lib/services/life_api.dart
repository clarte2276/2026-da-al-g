import 'dart:convert';

import 'package:http/http.dart' as http;

import 'ai_api_client.dart';
import 'auth_session.dart';

/// 안전·익명제보·라이프·정보 API 클라이언트 (sections 3–5).
class LifeApi {
  LifeApi({http.Client? httpClient, String? baseUrl})
    : _httpClient = httpClient ?? http.Client(),
      _ownsClient = httpClient == null,
      baseUrl = (baseUrl ?? AiApiClient.defaultBaseUrl).replaceFirst(RegExp(r'/+$'), '');

  final http.Client _httpClient;
  final bool _ownsClient;
  final String baseUrl;

  void close() {
    if (_ownsClient) _httpClient.close();
  }

  // ── 안전: Alerts ──

  Future<List<Map<String, dynamic>>> fetchAlerts() async =>
      (await _send('GET', '/api/alerts') as List).cast<Map<String, dynamic>>();

  Future<void> createAlert(Map<String, dynamic> body) async =>
      await _send('POST', '/api/alerts', body: body);

  Future<void> deleteAlert(String id) async =>
      await _send('DELETE', '/api/alerts/$id');

  // ── 안전: Hazards ──

  Future<List<Map<String, dynamic>>> fetchHazards({String? category}) async {
    final q = category != null ? '?category=$category' : '';
    return (await _send('GET', '/api/safety/hazards$q') as List).cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> fetchHazard(String id) async =>
      (await _send('GET', '/api/safety/hazards/$id')) as Map<String, dynamic>;

  Future<void> createHazard(Map<String, dynamic> body) async =>
      await _send('POST', '/api/safety/hazards', body: body);

  Future<void> addHazardComment(String id, String content) async =>
      await _send('POST', '/api/safety/hazards/$id/comments', body: {'content': content});

  Future<void> updateHazardStatus(String id, String status) async =>
      await _send('PATCH', '/api/safety/hazards/$id', body: {'status': status});

  // ── 안전: Tips ──

  Future<List<Map<String, dynamic>>> fetchTips() async =>
      (await _send('GET', '/api/safety/tips') as List).cast<Map<String, dynamic>>();

  Future<void> createTip(Map<String, dynamic> body) async =>
      await _send('POST', '/api/safety/tips', body: body);

  Future<void> deleteTip(String id) async =>
      await _send('DELETE', '/api/safety/tips/$id');

  // ── 익명 제보 (Voice) ──

  Future<List<Map<String, dynamic>>> fetchVoiceThreads() async =>
      (await _send('GET', '/api/voice') as List).cast<Map<String, dynamic>>();

  Future<void> createVoiceThread(String content) async =>
      await _send('POST', '/api/voice', body: {'content': content});

  Future<void> replyToVoice(String id, String content) async =>
      await _send('POST', '/api/voice/$id/replies', body: {'content': content});

  Future<List<Map<String, dynamic>>> fetchAllVoiceThreads() async =>
      (await _send('GET', '/api/admin/voice') as List).cast<Map<String, dynamic>>();

  // ── 뉴스 ──

  Future<List<Map<String, dynamic>>> fetchNews() async =>
      (await _send('GET', '/api/news') as List).cast<Map<String, dynamic>>();

  // ── 식당 메뉴 ──

  Future<List<Map<String, dynamic>>> fetchMenus() async =>
      (await _send('GET', '/api/life/menu') as List).cast<Map<String, dynamic>>();

  String menuFileUrl(String id) => '$baseUrl/api/life/menu/$id/file';

  Map<String, String> get authHeaders {
    final bearer = AuthSession.current?.accessToken;
    return bearer == null || bearer.isEmpty ? {} : {'Authorization': 'Bearer $bearer'};
  }

  Future<void> uploadMenu(String week, String filename, List<int> bytes) async {
    final request = http.MultipartRequest('POST', Uri.parse('$baseUrl/api/life/menu'))
      ..headers.addAll(authHeaders)
      ..fields['week'] = week
      ..files.add(http.MultipartFile.fromBytes('file', bytes, filename: filename));
    final response = await http.Response.fromStream(await _httpClient.send(request).timeout(const Duration(seconds: 60)));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw AiApiException(_errorMessage(response), statusCode: response.statusCode);
    }
  }

  // ── 비상 연락처 ──

  Future<List<Map<String, dynamic>>> fetchContacts() async =>
      (await _send('GET', '/api/contacts') as List).cast<Map<String, dynamic>>();

  Future<void> updateContacts(List<Map<String, dynamic>> contacts) async =>
      await _send('PUT', '/api/contacts', body: contacts);

  // ── 교육 영상 ──

  Future<List<Map<String, dynamic>>> fetchEduVideos() async =>
      (await _send('GET', '/api/edu/videos') as List).cast<Map<String, dynamic>>();

  Future<void> createEduVideo(Map<String, dynamic> body) async =>
      await _send('POST', '/api/edu/videos', body: body);

  Future<void> deleteEduVideo(String id) async =>
      await _send('DELETE', '/api/edu/videos/$id');

  // ── 실시간 열차 ──

  Future<List<Map<String, dynamic>>> fetchTrains() async =>
      (await _send('GET', '/api/realtime/trains') as List).cast<Map<String, dynamic>>();

  // ── 게임 점수 ──

  Future<void> postScore(String game, int score) async =>
      await _send('POST', '/api/games/scores', body: {'game': game, 'score': score});

  Future<List<Map<String, dynamic>>> fetchScores(String game) async =>
      (await _send('GET', '/api/games/scores?game=$game') as List).cast<Map<String, dynamic>>();

  // ── 내부 ──

  Future<Object?> _send(
    String method,
    String path, {
    Object? body,
    Duration timeout = const Duration(seconds: 30),
  }) async {
    final request = http.Request(method, Uri.parse('$baseUrl$path'));
    final bearer = AuthSession.current?.accessToken;
    if (bearer != null && bearer.isNotEmpty) {
      request.headers['Authorization'] = 'Bearer $bearer';
    }
    if (body != null) {
      request.headers['Content-Type'] = 'application/json';
      request.body = jsonEncode(body);
    }
    final response = await http.Response.fromStream(
      await _httpClient.send(request).timeout(timeout),
    );
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw AiApiException(
        _errorMessage(response),
        statusCode: response.statusCode,
      );
    }
    if (response.body.trim().isEmpty) return null;
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    return decoded;
  }

  static String _errorMessage(http.Response response) {
    try {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is Map<String, dynamic>) {
        final detail = decoded['detail'];
        if (detail is String && detail.isNotEmpty) return detail;
      }
    } catch (_) {}
    return 'HTTP ${response.statusCode}: ${response.body}';
  }
}
