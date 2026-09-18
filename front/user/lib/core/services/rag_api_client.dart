import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';
import '../models/rag_models.dart';

class RagApiException implements Exception {
  const RagApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class RagApiClient {
  RagApiClient({String? baseUrl, String? token})
    : baseUrl = (baseUrl ?? defaultApiBaseUrl()).replaceAll(RegExp(r'/+$'), '') {
    _token = token;
  }

  final String baseUrl;
  String? _token;

  bool get isAuthenticated => _token?.isNotEmpty == true;

  void clearToken() => _token = null;

  Map<String, String> _headers([Map<String, String>? extra]) {
    final headers = <String, String>{...?extra};
    if (isAuthenticated) headers['Authorization'] = 'Bearer $_token';
    return headers;
  }

  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  Future<String> health() async {
    final response = await http
        .get(_uri('/health'), headers: _headers())
        .timeout(const Duration(seconds: 10));
    final body = _decode(response);
    return body['embedding_provider']?.toString() ?? 'unknown';
  }

  Future<AuthSession> login(String username, String password) async {
    final response = await http
        .post(
          _uri('/api/auth/login'),
          headers: _headers({'Content-Type': 'application/json'}),
          body: jsonEncode({'username': username, 'password': password}),
        )
        .timeout(const Duration(seconds: 15));
    final session = AuthSession.fromJson(_decode(response));
    _token = session.accessToken;
    return session;
  }

  Future<AuthSession> register(
    String username,
    String password, {
    String? displayName,
  }) async {
    final response = await http
        .post(
          _uri('/api/auth/register'),
          headers: _headers({'Content-Type': 'application/json'}),
          body: jsonEncode({
            'username': username,
            'password': password,
            if (displayName != null && displayName.trim().isNotEmpty)
              'display_name': displayName.trim(),
          }),
        )
        .timeout(const Duration(seconds: 15));
    final session = AuthSession.fromJson(_decode(response));
    _token = session.accessToken;
    return session;
  }

  Future<AuthUser> me() async {
    final response = await http
        .get(_uri('/api/auth/me'), headers: _headers())
        .timeout(const Duration(seconds: 10));
    return AuthUser.fromJson(_decode(response));
  }

  Future<void> logout() async {
    if (!isAuthenticated) return;
    try {
      await http
          .post(_uri('/api/auth/logout'), headers: _headers())
          .timeout(const Duration(seconds: 10));
    } finally {
      clearToken();
    }
  }

  Future<ChatResponse> ask(
    String message, {
    List<Map<String, String>> history = const [],
  }) async {
    final response = await http
        .post(
          _uri('/api/chat'),
          headers: _headers({'Content-Type': 'application/json'}),
          body: jsonEncode({
            'message': message,
            'history': history,
            'top_k': 5,
            'max_hops': 2,
          }),
        )
        .timeout(const Duration(seconds: 90));
    return ChatResponse.fromJson(_decode(response));
  }

  /// Fetch the original document page an evidence chunk came from, as a PNG.
  ///
  /// The first request for a document may start a LibreOffice conversion that
  /// takes minutes; the server answers 202 until the page image is ready.
  Future<Uint8List> evidencePage(
    RagEvidence evidence, {
    int width = 1200,
    Duration limit = const Duration(minutes: 15),
  }) async {
    final documentId = evidence.documentId;
    if (documentId == null) {
      throw const RagApiException('근거의 원본 문서를 알 수 없습니다.');
    }
    final uri = _uri('/api/documents/$documentId/page.png').replace(
      queryParameters: {
        if (evidence.versionId != null) 'version_id': evidence.versionId!,
        if (evidence.page != null) 'page': '${evidence.page}',
        if (evidence.page == null) 'quote': evidence.text.trim(),
        'width': '$width',
      },
    );
    final deadline = DateTime.now().add(limit);
    while (true) {
      final response = await http
          .get(uri, headers: _headers())
          .timeout(const Duration(seconds: 60));
      if (response.statusCode == 200) return response.bodyBytes;
      if (response.statusCode == 202 && DateTime.now().isBefore(deadline)) {
        await Future<void>.delayed(const Duration(seconds: 3));
        continue;
      }
      dynamic decoded;
      try {
        decoded = jsonDecode(utf8.decode(response.bodyBytes));
      } on FormatException {
        decoded = null;
      }
      throw RagApiException(
        (decoded is Map ? decoded['detail']?.toString() : null) ??
            '원본 페이지를 불러오지 못했습니다. (${response.statusCode})',
        statusCode: response.statusCode,
      );
    }
  }

  Map<String, dynamic> _decode(http.Response response) {
    dynamic decoded;
    try {
      decoded = jsonDecode(response.body);
    } on FormatException {
      decoded = null;
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = decoded is Map ? decoded['detail'] : null;
      throw RagApiException(
        detail?.toString() ?? '서버 오류가 발생했습니다. (${response.statusCode})',
        statusCode: response.statusCode,
      );
    }
    if (decoded is! Map) {
      throw RagApiException(
        '서버 응답 형식이 올바르지 않습니다.',
        statusCode: response.statusCode,
      );
    }
    return Map<String, dynamic>.from(decoded);
  }
}
