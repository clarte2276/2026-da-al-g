import 'dart:convert';

import 'package:http/http.dart' as http;

import 'ai_api_client.dart';
import 'auth_session.dart';

/// 승무원 부가기능 API 클라이언트 (근무 교체 / 대기충당확인).
/// [AiApiClient]의 에러 처리를 그대로 따른다.
class CrewApi {
  CrewApi({http.Client? httpClient, String? baseUrl})
    : _httpClient = httpClient ?? http.Client(),
      _ownsClient = httpClient == null,
      _baseUrl = (baseUrl ?? AiApiClient.defaultBaseUrl).replaceFirst(RegExp(r'/+$'), '');

  final http.Client _httpClient;
  final bool _ownsClient;
  final String _baseUrl;

  // ── 근무 교체 ──────────────────────────────────────────────

  Future<List<Map<String, dynamic>>> fetchExchangePosts({
    String? status,
    bool? mine,
  }) async {
    final params = <String, String>{};
    if (status != null) params['status'] = status;
    if (mine == true) params['mine'] = 'true';
    final uri = Uri.parse('$_baseUrl/api/exchange/posts').replace(queryParameters: params.isNotEmpty ? params : null);
    return _getList(uri);
  }

  Future<Map<String, dynamic>> createExchangePost(Map<String, dynamic> body) async {
    return await _send('POST', '/api/exchange/posts', body: body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> respondToPost(String postId, {required String action, String? reason}) async {
    return await _send('POST', '/api/exchange/posts/$postId/respond', body: {
      'action': action,
      'reason': ?reason,
    }) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> volunteer(String postId) async {
    return await _send('POST', '/api/exchange/posts/$postId/volunteers', body: {}) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> acceptVolunteer(String postId, String volunteerId) async {
    return await _send('POST', '/api/exchange/posts/$postId/volunteers/$volunteerId/accept') as Map<String, dynamic>;
  }

  Future<void> deletePost(String postId) async {
    await _send('DELETE', '/api/exchange/posts/$postId');
  }

  Future<List<Map<String, dynamic>>> matchExchange({
    required String date,
    required String kind,
  }) async {
    final uri = Uri.parse('$_baseUrl/api/exchange/match').replace(
      queryParameters: {'date': date, 'kind': kind},
    );
    return _getList(uri);
  }

  // ── 대기충당확인 ──────────────────────────────────────────

  Future<List<Map<String, dynamic>>> fetchStandbyCoverage({String? date}) async {
    final uri = Uri.parse('$_baseUrl/api/standby-coverage').replace(
      queryParameters: date != null ? {'date': date} : null,
    );
    return _getList(uri);
  }

  Future<Map<String, dynamic>> uploadStandbyCoverage({
    required String date,
    required List<int> fileBytes,
    required String filename,
  }) async {
    final uri = Uri.parse('$_baseUrl/api/standby-coverage');
    final request = http.MultipartRequest('POST', uri);
    final bearer = AuthSession.current?.accessToken;
    if (bearer != null && bearer.isNotEmpty) {
      request.headers['Authorization'] = 'Bearer $bearer';
    }
    request.fields['date'] = date;
    request.files.add(http.MultipartFile.fromBytes('file', fileBytes, filename: filename));
    final streamed = await request.send().timeout(const Duration(seconds: 60));
    final response = await http.Response.fromStream(streamed);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw AiApiException(_errorMessage(response), statusCode: response.statusCode);
    }
    return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
  }

  Future<void> deleteStandbyCoverage(String id) async {
    await _send('DELETE', '/api/standby-coverage/$id');
  }

  /// 대기충당 이미지 URL (Authorization 헤더 필요).
  String standbyCoverageImageUrl(String id) => '$_baseUrl/api/standby-coverage/$id/image';

  // ── 내부 ──────────────────────────────────────────────────

  Future<List<Map<String, dynamic>>> _getList(Uri uri) async {
    final bearer = AuthSession.current?.accessToken;
    final response = await _httpClient.get(uri, headers: {
      if (bearer != null && bearer.isNotEmpty) 'Authorization': 'Bearer $bearer',
    }).timeout(const Duration(seconds: 30));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw AiApiException(_errorMessage(response), statusCode: response.statusCode);
    }
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    return (decoded as List).cast<Map<String, dynamic>>();
  }

  Future<Object?> _send(
    String method,
    String path, {
    Object? body,
    Duration timeout = const Duration(seconds: 30),
  }) async {
    final request = http.Request(method, Uri.parse('$_baseUrl$path'));
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
      throw AiApiException(_errorMessage(response), statusCode: response.statusCode);
    }
    if (response.body.isEmpty) return null;
    return jsonDecode(utf8.decode(response.bodyBytes));
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

  void close() {
    if (_ownsClient) _httpClient.close();
  }
}
