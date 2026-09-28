import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'auth_session.dart';

/// 현재 백엔드(`back/app`)의 `/api/*` 엔드포인트에 연결하는 클라이언트.
class AiApiClient {
  AiApiClient({http.Client? httpClient, String? baseUrl})
    : _httpClient = httpClient ?? http.Client(),
      _ownsClient = httpClient == null,
      baseUrl = _normalizeBaseUrl(baseUrl ?? defaultBaseUrl);

  static const _configuredBaseUrl = String.fromEnvironment('API_BASE_URL');

  static String get defaultBaseUrl => _configuredBaseUrl.trim().isNotEmpty
      ? _configuredBaseUrl.trim()
      : 'https://2026-da-al-g-production.up.railway.app';

  final http.Client _httpClient;
  final bool _ownsClient;
  final String baseUrl;

  Future<AiChatResponse> ask(
    String question, {
    List<Map<String, String>> history = const [],
  }) async {
    final decoded = await _send(
      'POST',
      '/api/chat',
      body: {'message': question, 'history': history},
      timeout: const Duration(seconds: 90),
    );
    return AiChatResponse.fromJson(decoded as Map<String, dynamic>);
  }

  /// 백엔드 계정은 username 기반이므로 사번을 username, 이름을 display_name 으로 보낸다.
  /// 이메일·노선은 서버에 저장되지 않아 로컬 세션에만 남긴다.
  Future<AuthResponse> signUp({
    required String name,
    required String employeeId,
    required String email,
    required String password,
    required String line,
  }) async {
    final decoded = await _send(
      'POST',
      '/api/auth/register',
      body: {
        'username': employeeId,
        'password': password,
        'display_name': name,
      },
    );
    final response = AuthResponse.fromJson(decoded as Map<String, dynamic>);
    return response.withUser(response.user.copyWith(email: email, line: line));
  }

  Future<AuthResponse> login({
    required String identifier,
    required String password,
  }) async {
    final decoded = await _send(
      'POST',
      '/api/auth/login',
      body: {'username': identifier, 'password': password},
    );
    return AuthResponse.fromJson(decoded as Map<String, dynamic>);
  }

  Future<void> logout(String accessToken) async {
    await _send('POST', '/api/auth/logout', token: accessToken);
  }

  Future<AuthUser> fetchCurrentUser(String accessToken) async {
    final decoded = await _send('GET', '/api/auth/me', token: accessToken);
    return AuthUser.fromJson(decoded as Map<String, dynamic>);
  }

  /// 규정 목록 = 서버에 적재된 문서 목록.
  Future<List<Map<String, dynamic>>> fetchRegulations() async {
    final decoded = await _send('GET', '/api/documents');
    return (decoded as List).whereType<Map<String, dynamic>>().map((doc) {
      final filename = doc['filename'] as String? ?? '';
      final dot = filename.lastIndexOf('.');
      return {
        'id': doc['id'],
        'title': dot > 0 ? filename.substring(0, dot) : filename,
        'category': dot > 0 ? filename.substring(dot + 1).toUpperCase() : '문서',
      };
    }).toList();
  }

  /// 규정 원문 = 최신 버전 조각(fragment)들의 텍스트를 순서대로 이어붙인 것.
  Future<Map<String, dynamic>> fetchRegulationDocument(String id) async {
    final decoded = await _send('GET', '/api/documents/$id/fragments');
    final texts = (decoded as List)
        .whereType<Map<String, dynamic>>()
        .map((f) => (f['text'] as String? ?? '').trim())
        .where((t) => t.isNotEmpty);
    return {'content': texts.join('\n\n'), 'annexes': const []};
  }

  void close() {
    if (_ownsClient) {
      _httpClient.close();
    }
  }

  Future<Object?> _send(
    String method,
    String path, {
    Object? body,
    String? token,
    Duration timeout = const Duration(seconds: 30),
  }) async {
    final request = http.Request(method, Uri.parse('$baseUrl$path'));
    final bearer = token ?? AuthSession.current?.accessToken;
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
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    if (decoded is! Map<String, dynamic> && decoded is! List) {
      throw const AiApiException('Invalid API response shape.');
    }
    return decoded;
  }

  static String _errorMessage(http.Response response) {
    try {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is Map<String, dynamic>) {
        final detail = decoded['detail'];
        if (detail is String && detail.isNotEmpty) {
          return detail;
        }
      }
    } catch (_) {
      // Fall back to the raw response below.
    }
    return 'HTTP ${response.statusCode}: ${response.body}';
  }

  static String _normalizeBaseUrl(String value) =>
      value.replaceFirst(RegExp(r'/+$'), '');
}

class AuthResponse {
  const AuthResponse({
    required this.accessToken,
    required this.tokenType,
    required this.user,
    this.expiresAt,
  });

  final String accessToken;
  final String tokenType;
  final AuthUser user;
  final DateTime? expiresAt;

  bool get isExpired =>
      expiresAt != null && !expiresAt!.isAfter(DateTime.now().toUtc());

  AuthResponse withUser(AuthUser user) => AuthResponse(
    accessToken: accessToken,
    tokenType: tokenType,
    user: user,
    expiresAt: expiresAt,
  );

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    final rawUser = json['user'];
    if (rawUser is! Map<String, dynamic>) {
      throw const AiApiException('Invalid auth user response shape.');
    }
    return AuthResponse(
      accessToken: json['access_token'] as String? ?? '',
      tokenType: json['token_type'] as String? ?? 'bearer',
      user: AuthUser.fromJson(rawUser),
      expiresAt: DateTime.tryParse(json['expires_at'] as String? ?? ''),
    );
  }

  Map<String, dynamic> toJson() => {
    'access_token': accessToken,
    'token_type': tokenType,
    if (expiresAt != null) 'expires_at': expiresAt!.toIso8601String(),
    'user': user.toJson(),
  };
}

class AuthUser {
  const AuthUser({
    required this.id,
    required this.name,
    required this.employeeId,
    required this.email,
    required this.line,
  });

  final String id;
  final String name;
  final String employeeId;
  final String email;
  final String line;

  AuthUser copyWith({String? email, String? line}) => AuthUser(
    id: id,
    name: name,
    employeeId: employeeId,
    email: email ?? this.email,
    line: line ?? this.line,
  );

  // 서버 응답(username/display_name)과 로컬 저장 형식(name/employee_id) 모두 읽는다.
  factory AuthUser.fromJson(Map<String, dynamic> json) {
    return AuthUser(
      id: json['id']?.toString() ?? '',
      name: json['display_name'] as String? ?? json['name'] as String? ?? '',
      employeeId:
          json['username'] as String? ?? json['employee_id'] as String? ?? '',
      email: json['email'] as String? ?? '',
      line: json['line'] as String? ?? '6호선',
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'employee_id': employeeId,
    'email': email,
    'line': line,
  };
}

class AiChatResponse {
  const AiChatResponse({
    required this.answer,
    required this.mode,
    required this.sources,
  });

  final String answer;
  final String mode;
  final List<AiEvidenceSource> sources;

  factory AiChatResponse.fromJson(Map<String, dynamic> json) {
    final rawSources = json['evidence'];
    return AiChatResponse(
      answer: json['answer'] as String? ?? '',
      mode: json['mode'] as String? ?? 'rag',
      sources: rawSources is List
          ? rawSources
                .whereType<Map<String, dynamic>>()
                .map(AiEvidenceSource.fromJson)
                .toList()
          : const [],
    );
  }
}

class AiEvidenceSource {
  const AiEvidenceSource({
    required this.score,
    required this.title,
    required this.fileName,
    this.content,
    this.linkedAnnex,
    this.sourcePath,
    this.chunkId,
    this.retriever,
  });

  final double score;
  final String title;
  final String fileName;
  final String? content;
  final String? linkedAnnex;
  final String? sourcePath;
  final String? chunkId;
  final String? retriever;

  /// 백엔드 `EvidenceOut` → 레거시 화면이 쓰는 근거 형태.
  factory AiEvidenceSource.fromJson(Map<String, dynamic> json) {
    final fragment = json['fragment'] as Map<String, dynamic>?;
    final hop = (json['hop'] as num?)?.toInt() ?? 0;
    return AiEvidenceSource(
      score: (json['score'] as num?)?.toDouble() ?? 0,
      title:
          json['location'] as String? ??
          fragment?['title'] as String? ??
          '제목 없음',
      fileName: json['filename'] as String? ?? '알 수 없음',
      content: json['text'] as String? ?? fragment?['text'] as String?,
      linkedAnnex: json['via_relation'] as String?,
      sourcePath: json['filename'] as String?,
      chunkId: fragment?['id'] as String? ?? json['link_id'] as String?,
      retriever: hop == 0 ? '직접 검색' : '그래프 $hop hop',
    );
  }
}

class AiApiException implements Exception {
  const AiApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}
