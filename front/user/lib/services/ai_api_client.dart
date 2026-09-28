import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

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

  /// 답변 스트림(NDJSON): status·delta 이벤트가 오고, 마지막 done에 인용을 정리한 최종 답변과 근거가 온다.
  Stream<AiChatEvent> askStream(
    String question, {
    List<Map<String, String>> history = const [],
  }) async* {
    final request = http.Request('POST', Uri.parse('$baseUrl/api/chat/stream'));
    final bearer = AuthSession.current?.accessToken;
    if (bearer != null && bearer.isNotEmpty) {
      request.headers['Authorization'] = 'Bearer $bearer';
    }
    request.headers['Content-Type'] = 'application/json';
    request.body = jsonEncode({'message': question, 'history': history});

    final response = await _httpClient
        .send(request)
        .timeout(const Duration(seconds: 30));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw AiApiException(
        _errorMessage(await http.Response.fromStream(response)),
        statusCode: response.statusCode,
      );
    }
    // 조각 사이가 60초 넘게 비면 끊긴 것으로 본다(TimeoutException).
    final lines = response.stream
        .timeout(const Duration(seconds: 60))
        .transform(utf8.decoder)
        .transform(const LineSplitter());
    await for (final line in lines) {
      if (line.trim().isEmpty) continue;
      final json = jsonDecode(line) as Map<String, dynamic>;
      final text = json['text'] as String? ?? '';
      switch (json['type']) {
        case 'status':
          yield AiChatEvent.status(text);
        case 'delta':
          yield AiChatEvent.delta(text);
        case 'done':
          yield AiChatEvent.done(AiChatResponse.fromJson(json));
          return;
      }
    }
    throw const AiApiException('답변이 중간에 끊겼습니다.');
  }

  /// 답변 평가(👍/👎)를 서버 감사 로그에 남긴다.
  Future<void> sendFeedback({
    required String rating,
    required String question,
    required String answer,
    required List<Map<String, dynamic>> evidence,
    String? reason,
  }) async {
    await _send(
      'POST',
      '/api/chat/feedback',
      body: {
        'rating': rating,
        'question': question,
        'answer': answer,
        'evidence': evidence,
        'reason': ?reason,
      },
    );
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

  /// 비밀번호 변경. 성공하면 서버가 다른 기기의 로그인을 끊는다.
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    await _send(
      'POST',
      '/api/auth/password',
      body: {
        'current_password': currentPassword,
        'new_password': newPassword,
      },
    );
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

  /// 원문 페이지 PNG. 첫 변환 중(202)이면 준비될 때까지 다시 요청한다.
  /// page 가 없으면 서버가 quote 로 페이지를 찾는다.
  Future<Uint8List> fetchPageImage(
    String documentId, {
    String? versionId,
    int? page,
    String? quote,
  }) async {
    final uri = Uri.parse('$baseUrl/api/documents/$documentId/page.png').replace(
      queryParameters: {
        if (versionId != null) 'version_id': versionId,
        if (page != null) 'page': '$page',
        if (page == null && quote != null) 'quote': quote,
      },
    );
    final bearer = AuthSession.current?.accessToken;
    for (var attempt = 0; attempt < 12; attempt++) {
      final response = await _httpClient
          .get(uri, headers: {
            if (bearer != null && bearer.isNotEmpty)
              'Authorization': 'Bearer $bearer',
          })
          .timeout(const Duration(seconds: 30));
      if (response.statusCode == 202) continue;
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw AiApiException(
          _errorMessage(response),
          statusCode: response.statusCode,
        );
      }
      return response.bodyBytes;
    }
    throw const AiApiException('원문 변환이 아직 끝나지 않았습니다.');
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

enum AiChatEventType { status, delta, done }

class AiChatEvent {
  const AiChatEvent.status(this.text)
    : type = AiChatEventType.status,
      response = null;
  const AiChatEvent.delta(this.text)
    : type = AiChatEventType.delta,
      response = null;
  const AiChatEvent.done(AiChatResponse this.response)
    : type = AiChatEventType.done,
      text = '';

  final AiChatEventType type;
  final String text;

  /// done 이벤트에만 있다.
  final AiChatResponse? response;
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
    this.documentId,
    this.versionId,
    this.page,
  });

  final double score;
  final String title;
  final String fileName;
  final String? content;
  final String? linkedAnnex;
  final String? sourcePath;
  final String? chunkId;
  final String? retriever;
  final String? documentId;
  final String? versionId;
  final int? page;

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
      documentId:
          json['document_id'] as String? ?? fragment?['document_id'] as String?,
      versionId:
          json['version_id'] as String? ?? fragment?['version_id'] as String?,
      page: (json['page'] as num?)?.toInt(),
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
