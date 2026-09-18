class ChatResponse {
  const ChatResponse({
    required this.answer,
    required this.mode,
    required this.evidence,
    required this.embeddingProvider,
    required this.graphExpanded,
  });

  final String answer;
  final String mode;
  final List<RagEvidence> evidence;
  final String embeddingProvider;
  final bool graphExpanded;

  factory ChatResponse.fromJson(Map<String, dynamic> json) {
    final rawEvidence = json['evidence'];
    final evidence = rawEvidence is List
        ? rawEvidence
              .whereType<Map>()
              .map(
                (item) => RagEvidence.fromJson(Map<String, dynamic>.from(item)),
              )
              .toList()
        : <RagEvidence>[];
    return ChatResponse(
      answer: json['answer']?.toString() ?? '답변을 생성하지 못했습니다.',
      mode: json['mode']?.toString() ?? 'rag',
      evidence: evidence,
      embeddingProvider: json['embedding_provider']?.toString() ?? 'unknown',
      graphExpanded: json['graph_expanded'] == true,
    );
  }
}

class AuthUser {
  const AuthUser({
    required this.id,
    required this.username,
    required this.displayName,
    required this.role,
    required this.isActive,
  });

  final String id;
  final String username;
  final String displayName;
  final String role;
  final bool isActive;

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    return AuthUser(
      id: json['id']?.toString() ?? '',
      username: json['username']?.toString() ?? '',
      displayName: json['display_name']?.toString() ?? '',
      role: json['role']?.toString() ?? 'user',
      isActive: json['is_active'] != false,
    );
  }
}

class AuthSession {
  const AuthSession({
    required this.accessToken,
    required this.expiresAt,
    required this.user,
  });

  final String accessToken;
  final DateTime expiresAt;
  final AuthUser user;

  factory AuthSession.fromJson(Map<String, dynamic> json) {
    return AuthSession(
      accessToken: json['access_token']?.toString() ?? '',
      expiresAt: DateTime.tryParse(json['expires_at']?.toString() ?? '') ??
          DateTime.now().toUtc(),
      user: AuthUser.fromJson(
        Map<String, dynamic>.from(json['user'] as Map? ?? const {}),
      ),
    );
  }
}

class RagEvidence {
  const RagEvidence({
    required this.text,
    required this.score,
    required this.hop,
    required this.filename,
    required this.fragment,
    this.location,
    this.documentId,
    this.versionId,
    this.page,
    this.viaRelation,
    this.linkId,
  });

  final String text;
  final double score;
  final int hop;
  final String? filename;
  final Map<String, dynamic>? fragment;
  final String? location;
  final String? documentId;
  final String? versionId;
  final int? page;
  final String? viaRelation;
  final String? linkId;

  factory RagEvidence.fromJson(Map<String, dynamic> json) {
    final rawFragment = json['fragment'];
    final fragment = rawFragment is Map
        ? Map<String, dynamic>.from(rawFragment)
        : null;
    return RagEvidence(
      text: json['text']?.toString() ?? fragment?['text']?.toString() ?? '',
      score: (json['score'] as num?)?.toDouble() ?? 0,
      hop: (json['hop'] as num?)?.toInt() ?? 0,
      filename: json['filename']?.toString(),
      fragment: fragment,
      location: json['location']?.toString(),
      documentId: json['document_id']?.toString(),
      versionId: json['version_id']?.toString(),
      page: (json['page'] as num?)?.toInt(),
      viaRelation: json['via_relation']?.toString(),
      linkId: json['link_id']?.toString(),
    );
  }

  String get sourceLabel {
    final title = fragment?['title']?.toString();
    return filename ?? (title?.isNotEmpty == true ? title! : '문서 근거');
  }

  String get locationLabel {
    if (location?.isNotEmpty == true) return location!;
    final locator = fragment?['locator_json'];
    if (locator is Map) {
      if (locator['page'] != null) return '페이지 ${locator['page']}';
      if (locator['slide'] != null) return '슬라이드 ${locator['slide']}';
      if (locator['article'] != null) return locator['article'].toString();
    }
    return hop == 0 ? '직접 검색 근거' : '그래프 $hop hop 연결 근거';
  }

  bool get hasSource => documentId != null && (page != null || text.trim().isNotEmpty);

  String get originLabel =>
      hop == 0 ? '직접 검색 근거' : '그래프 $hop hop 연결 근거';
}

class ChatMessage {
  const ChatMessage({
    required this.text,
    required this.isUser,
    this.response,
    this.isError = false,
  });

  final String text;
  final bool isUser;
  final ChatResponse? response;
  final bool isError;
}
