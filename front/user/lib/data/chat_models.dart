class ChatSource {
  final String regulation;
  final String chapter;
  final String version;
  final String? excerpt;
  final String? content;
  final String? sourcePath;
  final String? chunkId;
  final String? retriever;
  final String? documentId;
  final String? versionId;
  final int? page;

  /// 그래프로 간접 연결된 근거. 직접 검색된 근거와 구분해 표시한다.
  bool get isRelated => retriever?.startsWith('그래프') ?? false;

  ChatSource({
    required this.regulation,
    required this.chapter,
    required this.version,
    this.excerpt,
    this.content,
    this.sourcePath,
    this.chunkId,
    this.retriever,
    this.documentId,
    this.versionId,
    this.page,
  });

  factory ChatSource.fromJson(Map<String, dynamic> j) => ChatSource(
    regulation: j['regulation'],
    chapter: j['chapter'],
    version: j['version'],
    excerpt: j['excerpt'],
    content: j['content'],
    sourcePath: j['sourcePath'],
    chunkId: j['chunkId'],
    retriever: j['retriever'],
    documentId: j['documentId'],
    versionId: j['versionId'],
    page: j['page'],
  );

  Map<String, dynamic> toJson() => {
    'regulation': regulation,
    'chapter': chapter,
    'version': version,
    if (excerpt != null) 'excerpt': excerpt,
    if (content != null) 'content': content,
    if (sourcePath != null) 'sourcePath': sourcePath,
    if (chunkId != null) 'chunkId': chunkId,
    if (retriever != null) 'retriever': retriever,
    if (documentId != null) 'documentId': documentId,
    if (versionId != null) 'versionId': versionId,
    if (page != null) 'page': page,
  };
}

class ChatMsg {
  final bool isUser;
  final String text;
  final List<ChatSource> sources;
  final bool isError;

  /// 사용자가 남긴 평가: 'up' | 'down' | null.
  String? rating;

  ChatMsg({
    required this.isUser,
    required this.text,
    ChatSource? source,
    List<ChatSource>? sources,
    this.isError = false,
    this.rating,
  }) : sources = sources ?? [?source];

  // 예전 기록은 근거가 'source' 하나로 저장돼 있다.
  factory ChatMsg.fromJson(Map<String, dynamic> j) => ChatMsg(
    isUser: j['isUser'],
    text: j['text'],
    sources: [
      for (final s in (j['sources'] as List?) ?? [?j['source']])
        ChatSource.fromJson(s as Map<String, dynamic>),
    ],
    isError: j['isError'] ?? false,
    rating: j['rating'],
  );

  Map<String, dynamic> toJson() => {
    'isUser': isUser,
    'text': text,
    if (sources.isNotEmpty) 'sources': [for (final s in sources) s.toJson()],
    if (isError) 'isError': true,
    'rating': ?rating,
  };
}

class Conversation {
  final String id;
  final String title;
  final DateTime createdAt;
  final List<ChatMsg> messages;

  Conversation({
    required this.id,
    required this.title,
    required this.createdAt,
    required this.messages,
  });

  String get timeAgo {
    final diff = DateTime.now().difference(createdAt);
    if (diff.inMinutes < 2) return '방금';
    if (diff.inHours < 1) return '${diff.inMinutes}분 전';
    if (diff.inDays == 0) return '오늘';
    if (diff.inDays == 1) return '어제';
    if (diff.inDays < 7) return '${diff.inDays}일 전';
    return '${(diff.inDays / 7).floor()}주일 전';
  }

  String get preview {
    final last = messages.lastWhere(
      (m) => !m.isUser,
      orElse: () => messages.last,
    );
    return last.text.length > 55 ? '${last.text.substring(0, 55)}…' : last.text;
  }

  factory Conversation.fromJson(Map<String, dynamic> j) => Conversation(
    id: j['id'],
    title: j['title'],
    createdAt: DateTime.parse(j['createdAt']),
    messages: (j['messages'] as List)
        .map((m) => ChatMsg.fromJson(m as Map<String, dynamic>))
        .toList(),
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'createdAt': createdAt.toIso8601String(),
    'messages': messages.map((m) => m.toJson()).toList(),
  };
}

Conversation newConversationFrom(String firstMessage) => Conversation(
  id: DateTime.now().millisecondsSinceEpoch.toString(),
  title: firstMessage.length > 20 ? '${firstMessage.substring(0, 20)}…' : firstMessage,
  createdAt: DateTime.now(),
  messages: [ChatMsg(isUser: true, text: firstMessage)],
);
