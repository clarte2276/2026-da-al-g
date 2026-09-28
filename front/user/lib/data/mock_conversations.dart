class ChatSource {
  final String regulation;
  final String chapter;
  final String version;
  final String? excerpt;
  final String? content;
  final String? sourcePath;
  final String? chunkId;
  final String? retriever;

  ChatSource({
    required this.regulation,
    required this.chapter,
    required this.version,
    this.excerpt,
    this.content,
    this.sourcePath,
    this.chunkId,
    this.retriever,
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
  };
}

class ChatMsg {
  final bool isUser;
  final String text;
  final ChatSource? source;

  ChatMsg({required this.isUser, required this.text, this.source});

  factory ChatMsg.fromJson(Map<String, dynamic> j) => ChatMsg(
    isUser: j['isUser'],
    text: j['text'],
    source: j['source'] != null ? ChatSource.fromJson(j['source'] as Map<String, dynamic>) : null,
  );

  Map<String, dynamic> toJson() => {
    'isUser': isUser,
    'text': text,
    if (source != null) 'source': source!.toJson(),
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

final _now = DateTime.now();

final List<Conversation> mockConversations = [
  Conversation(
    id: '1',
    title: '출입문 고장 시 승객 안내',
    createdAt: _now.subtract(const Duration(days: 1)),
    messages: [
      ChatMsg(isUser: true, text: '출입문 고장 시 승객 안내 기준은 어떻게 되나요?'),
      ChatMsg(
        isUser: false,
        text:
            '운전취급규정 제328조에 따르면 열차운전 중 출입문 고장이 발생하면 운전관제에 보고하고 안내방송을 실시해야 합니다. 이후 출입문 정상 작동을 위한 응급조치를 시행하고, 1개 이상의 출입문이 정상 작동하지 않으면 운전관제의 지시에 따라 회송 조치합니다.',
        source: ChatSource(
          regulation: '운전취급규정',
          chapter: '제328조 · 열차의 출입문 고장인 경우',
          version: '원문 기준',
          excerpt: '열차운전 중 출입문 고장이 발생하였을 때에는 운전관제에 보고하고 안내방송을 실시하여야 한다. 1. 안내방송을 실시한다. 2. 출입문이 정상 작동되도록 응급조치를 시행한다. 3. 출입문 1개 이상 정상 작동이 불가하면 운전관제의 지시에 따라 회송조치 하여야 한다.',
        ),
      ),
      ChatMsg(isUser: true, text: '표준 방송 문안 예시가 있나요?'),
      ChatMsg(
        isUser: false,
        text:
            '규정 원문에는 고정된 방송 문안까지는 제시되어 있지 않습니다. 다만 안내방송 실시와 승객안전 조치가 요구되므로, 실제 방송은 현장 상황을 반영해 간결하게 해야 합니다.\n\n예: "출입문 이상으로 안전 확인 중입니다. 승객 여러분께서는 안내에 따라 주시고, 해당 출입문 주변에서 물러나 주시기 바랍니다."\n\n관제업무내규는 출입문이 닫히지 않는 경우 회송 조치, 막차 등 예외 상황에서는 출입문 보호막 설치, 감시자 승차, 승객안내와 다른 객실 분승 유도 등 안전조치를 확인한 뒤 주의운전을 지시하도록 정하고 있습니다.',
        source: ChatSource(
          regulation: '관제업무내규',
          chapter: '제54조 · 고장열차의 조치',
          version: '원문 기준',
          excerpt: '출입문이 닫히지 않는 경우에는 회송 조치하여야 한다. 다만, 막차 등 부득이한 경우에는 출입문 보호막 설치, 감시자 승차, 승객안내 및 다른 객실 분승 유도 등 안전조치를 확인한 후 주의운전을 지시할 수 있다.',
        ),
      ),
    ],
  ),
  Conversation(
    id: '2',
    title: '당직근무 변경 신청 절차',
    createdAt: _now.subtract(const Duration(days: 2)),
    messages: [
      ChatMsg(isUser: true, text: '당직근무를 바꿔야 하면 어떻게 신청하나요?'),
      ChatMsg(
        isUser: false,
        text:
            '현업당직근무내규 제5조에 따르면 당직수명자가 출장, 휴가 등의 사유로 당직근무를 할 수 없을 때에는 당직근무 예정 2일 전까지 당직명령권자에게 당직변경을 신청해 승인을 받아야 합니다.\n\n다만 불가피한 사유가 발생한 경우에는 당직근무 개시 전까지 제출해 승인을 받을 수 있습니다.',
        source: ChatSource(
          regulation: '현업당직근무내규',
          chapter: '제5조 · 당직명령',
          version: '원문 기준',
          excerpt: '당직수명자가 출장·휴가 등의 사유로 당직근무를 할 수 없을 때에는 당직근무 예정일 2일 전까지 당직명령권자에게 당직변경을 신청하여 승인을 받아야 한다. 다만, 불가피한 사유가 발생한 경우에는 당직근무 개시 전까지 신청하여 승인을 받을 수 있다.',
        ),
      ),
      ChatMsg(isUser: true, text: '신청서 양식은 어디서 받나요?'),
      ChatMsg(
        isUser: false,
        text:
            '현재 확인한 규정 원문에는 당직변경 신청서의 다운로드 위치나 전자결재 처리 방법까지는 명시되어 있지 않습니다. 규정상 확실한 요건은 당직명령권자에게 신청하고 승인을 받는 절차이므로, 실제 양식과 제출 경로는 소속 부서의 당직명령권자 또는 현업의 장에게 확인하는 것이 맞습니다.',
        source: ChatSource(
          regulation: '현업당직근무내규',
          chapter: '제5조 · 당직명령',
          version: '원문 기준',
          excerpt: '당직수명자가 출장·휴가 등의 사유로 당직근무를 할 수 없을 때에는 당직근무 예정일 2일 전까지 당직명령권자에게 당직변경을 신청하여 승인을 받아야 한다.',
        ),
      ),
    ],
  ),
  Conversation(
    id: '3',
    title: '열차 지연 관제 보고 기준',
    createdAt: _now.subtract(const Duration(days: 3)),
    messages: [
      ChatMsg(isUser: true, text: '열차가 지연될 때 관제 보고는 언제 해야 하나요?'),
      ChatMsg(
        isUser: false,
        text:
            '운전취급규정 제35조는 차량 또는 운전설비의 결함, 기후상태 등으로 열차운행에 지장이 염려될 때 승무원이 지체 없이 운전관제에 보고하도록 정합니다.\n\n또한 관제업무내규 제21조는 열차사고나 운행장애 등으로 열차 지연 또는 지연이 예상될 때 기관사, 해당 역장, 관련 현업 소장에게 내용을 통보하고 필요한 조치를 하도록 정합니다.',
        source: ChatSource(
          regulation: '운전취급규정 / 관제업무내규',
          chapter: '운전취급규정 제35조, 관제업무내규 제21조',
          version: '원문 기준',
          excerpt: '승무원은 차량 또는 운전설비의 결함, 기후상태 등으로 열차운행에 지장이 염려될 때에는 지체 없이 운전관제에 보고하여야 한다. (운전취급규정 제35조) 운전관제는 열차사고·운행장애 등으로 열차 지연 또는 지연이 예상될 때 기관사, 역장, 관련 현업 소장에게 통보하고 필요한 조치를 하여야 한다. (관제업무내규 제21조)',
        ),
      ),
      ChatMsg(isUser: true, text: '보고 후 추가 조치 사항이 있나요?'),
      ChatMsg(
        isUser: false,
        text:
            '보고 후에는 관제업무내규 제21조에 따라 열차 지연 또는 지연 예상 사실을 관계자에게 통보하고, 적절한 조치와 이용 안내방송을 실시해야 합니다.\n\n철도사고 및 운행장애 조사처리규정 제6조는 전동열차 20분 이상 운행에 일시적 지장을 초래한 경우를 운행지연으로 봅니다. 같은 규정 제10조와 제11조는 사고 등이 발생하면 즉시 급보하고, 사고 개황은 가능한 6하 원칙에 따라 보고하도록 정합니다.',
        source: ChatSource(
          regulation: '관제업무내규 / 철도사고 및 운행장애 조사처리규정',
          chapter: '관제업무내규 제21조, 조사처리규정 제6조·제10조·제11조',
          version: '원문 기준',
          excerpt: '열차 지연 또는 지연이 예상되는 때에는 관계자에게 통보하고 이용 안내방송을 실시하여야 한다. 전동열차가 20분 이상 운행에 일시적 지장을 초래한 경우는 운행지연으로 보며, 사고 발생 시 즉시 급보하고 6하 원칙에 따라 보고하여야 한다.',
        ),
      ),
    ],
  ),
  Conversation(
    id: '4',
    title: '터널 내 비상 대피 절차',
    createdAt: _now.subtract(const Duration(days: 7)),
    messages: [
      ChatMsg(isUser: true, text: '터널 내 비상 상황 발생 시 대피 절차를 알려주세요'),
      ChatMsg(
        isUser: false,
        text:
            '관제업무내규 제55조는 역간에서 정차한 열차의 승객 하차 취급 절차를 정하고 있습니다.\n\n운전관제는 필요 시 전차선 단전, 인접선로 운행 열차에 대한 주의운전 또는 정차 지시, 관계 직원 파견 및 승객유도 지시, 승무원 통보 및 안내방송 지시를 해야 합니다.\n\n따라서 터널 등 역간에서 대피가 필요한 경우에는 임의로 비상문을 개방하기보다 관제 지시에 따라 단전·인접선 안전확보·직원 파견·안내방송을 먼저 확인하는 흐름이 맞습니다.',
        source: ChatSource(
          regulation: '관제업무내규',
          chapter: '제55조 · 역간에서 승객 하차 취급',
          version: '원문 기준',
          excerpt: '운전관제는 역간에서 정차한 열차의 승객 하차가 필요할 때 전차선 단전, 인접선로 열차에 주의운전 또는 정차 지시, 관계 직원 파견 및 승객유도 지시, 승무원 통보 및 안내방송을 지시하여야 한다.',
        ),
      ),
    ],
  ),
  Conversation(
    id: '5',
    title: '음주 측정 및 출무 불가 기준',
    createdAt: _now.subtract(const Duration(days: 14)),
    messages: [
      ChatMsg(isUser: true, text: '음주 측정 기준치가 어떻게 되나요?'),
      ChatMsg(
        isUser: false,
        text:
            '운전취급규정 제8조는 운전업무종사자, 관제업무종사자, 여객 승무서비스 제공자가 술을 마시거나 약물을 사용한 상태에서 업무를 수행해서는 안 된다고 정합니다.\n\n승무원지도운용내규 제47조와 제53조에 따르면 혈중알콜농도 법령기준치 이상이면 운전업무 제한 대상입니다. 업무 시작 전 적발되면 당일 업무중지와 지상근무 조치, 업무 수행 중 적발되면 업무중지 및 교대조치와 인사규정에 따른 징계요구·철도관련법상 행정처분 의뢰가 규정되어 있습니다.\n\n참고로 같은 내규 부칙은 음주자 혈중알콜농도 기준 수치가 2018년 2월 10일부터 0.03%에서 0.02%로 적용된다고 명시합니다.',
        source: ChatSource(
          regulation: '운전취급규정 / 승무원지도운용내규',
          chapter: '운전취급규정 제8조, 승무원지도운용내규 제47조·제53조·부칙',
          version: '원문 기준',
          excerpt: '혈중알콜농도 법령기준치 이상인 자는 운전업무 제한 대상이다. 업무 시작 전 적발 시 당일 업무중지 및 지상근무 조치하고, 업무 중 적발 시 업무중지 및 교대조치 후 인사규정에 따른 징계와 철도관련법 행정처분을 의뢰한다. 부칙: 음주 기준 수치는 2018년 2월 10일부터 혈중알콜농도 0.02% 이상으로 적용한다.',
        ),
      ),
    ],
  ),
];

Conversation newConversationFrom(String firstMessage) => Conversation(
  id: DateTime.now().millisecondsSinceEpoch.toString(),
  title: firstMessage.length > 20 ? '${firstMessage.substring(0, 20)}…' : firstMessage,
  createdAt: DateTime.now(),
  messages: [ChatMsg(isUser: true, text: firstMessage)],
);
