import 'dart:async';

import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../data/conversation_store.dart';
import '../data/chat_models.dart';
import '../services/ai_api_client.dart';
import '../widgets/evidence_source_card.dart';
import '../widgets/highlight_text.dart';
import 'regulation_viewer_screen.dart';

class ChatRoomScreen extends StatefulWidget {
  const ChatRoomScreen({super.key, required this.conversation});

  final Conversation conversation;

  @override
  State<ChatRoomScreen> createState() => _ChatRoomScreenState();
}

class _ChatRoomScreenState extends State<ChatRoomScreen> {
  final _scrollController = ScrollController();
  final _controller = TextEditingController();
  AiApiClient? _aiApiClient;
  late final List<ChatMsg> _messages;
  bool _isSending = false;

  /// 첫 답변 조각이 오기 전까지 보여줄 진행 문구. null이면 표시하지 않는다.
  String? _status;

  @override
  void initState() {
    super.initState();
    _messages = List.of(widget.conversation.messages);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _scrollToBottom();
      if (_messages.length == 1 && _messages.first.isUser) {
        _requestAnswer(_messages.first.text);
      }
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    _controller.dispose();
    _aiApiClient?.close();
    super.dispose();
  }

  Future<void> _showOptions() async {
    final wantDelete = await showModalBottomSheet<bool>(
      context: context,
      builder: (sheetCtx) => SafeArea(
        child: ListTile(
          leading: const Icon(Icons.delete_outline_rounded, color: Colors.red),
          title: const Text('채팅 삭제', style: TextStyle(color: Colors.red)),
          onTap: () => Navigator.pop(sheetCtx, true),
        ),
      ),
    );
    if (wantDelete != true || !mounted) return;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        title: const Text('채팅 삭제'),
        content: const Text('이 대화를 삭제하면 복구할 수 없습니다.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogCtx, false),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(dialogCtx, true),
            child: const Text('삭제', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
    if (confirmed == true && mounted) {
      ConversationStore.instance.remove(widget.conversation.id);
      Navigator.pop(context);
    }
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  void _scrollAfterBuild() {
    WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());
  }

  Future<void> _sendCurrentMessage() async {
    if (_isSending) {
      return;
    }

    final question = _controller.text.trim();
    if (question.isEmpty) {
      return;
    }

    setState(() {
      _controller.clear();
      _messages.add(ChatMsg(isUser: true, text: question));
    });
    _saveToStore();
    _scrollAfterBuild();

    await _requestAnswer(question);
  }

  Future<void> _requestAnswer(String question) async {
    if (_isSending) {
      return;
    }

    setState(() {
      _isSending = true;
      _status = '답변 준비 중';
    });
    _scrollAfterBuild();

    // 스트리밍 중인 답변 말풍선 위치. 실패하면 지우고 오류 메시지로 바꾼다.
    int? streamingIndex;
    var completed = false;
    try {
      // 방금 추가된 질문을 뺀 최근 대화 (서버 최대 12개).
      final previous = _messages
          .sublist(0, _messages.length - 1)
          .where((m) => m.text.trim().isNotEmpty);
      final history = previous
          .skip(previous.length > 12 ? previous.length - 12 : 0)
          .map(
            (m) => {'role': m.isUser ? 'user' : 'assistant', 'content': m.text},
          )
          .toList();
      final events = (_aiApiClient ??= AiApiClient()).askStream(
        question,
        history: history,
      );
      var streamed = '';
      void put(ChatMsg msg) {
        if (streamingIndex == null) {
          _messages.add(msg);
          streamingIndex = _messages.length - 1;
        } else {
          _messages[streamingIndex!] = msg;
        }
      }

      await for (final event in events) {
        if (!mounted) return;
        switch (event.type) {
          case AiChatEventType.status:
            if (streamingIndex == null) setState(() => _status = event.text);
          case AiChatEventType.delta:
            streamed += event.text;
            setState(() {
              _status = null;
              put(ChatMsg(isUser: false, text: streamed));
            });
            _scrollAfterBuild();
          case AiChatEventType.done:
            // 최종 답변은 인용 번호가 정리돼 있어 스트리밍된 글을 대체한다.
            final response = event.response!;
            setState(() {
              _status = null;
              put(
                ChatMsg(
                  isUser: false,
                  text: response.answer.isEmpty
                      ? '제공된 문서에서 확인되지 않습니다.'
                      : response.answer,
                  sources: response.sources.map(_sourceFrom).toList(),
                ),
              );
            });
            completed = true;
            _saveToStore();
        }
      }
    } on TimeoutException {
      _dropPartial(streamingIndex, completed);
      _appendErrorMessage('답변이 늦어지고 있습니다. 통신 상태를 확인한 뒤 다시 질문해 주세요.');
    } on AiApiException catch (error) {
      _dropPartial(streamingIndex, completed);
      _appendErrorMessage(
        error.statusCode == 401
            ? '로그인이 만료되었습니다. 다시 로그인해 주세요.'
            : '답변을 가져오지 못했습니다. 잠시 후 다시 질문해 주세요.',
      );
    } catch (_) {
      _dropPartial(streamingIndex, completed);
      _appendErrorMessage('서버에 연결하지 못했습니다. 통신 상태를 확인해 주세요.');
    } finally {
      if (mounted) {
        setState(() {
          _isSending = false;
          _status = null;
        });
        _scrollAfterBuild();
      }
    }
  }

  void _dropPartial(int? index, bool completed) {
    if (index != null && !completed && mounted) {
      setState(() => _messages.removeAt(index));
    }
  }

  Future<void> _rate(int index, String rating) async {
    // 스트리밍 중인 답변은 아직 최종본이 아니다.
    if (_isSending && index == _messages.length - 1) return;
    final msg = _messages[index];
    String? reason;
    if (rating == 'down') {
      reason = await _askReason();
      if (reason == null || !mounted) return;
      reason = reason.trim().isEmpty ? null : reason.trim();
    }
    final question = _messages
        .take(index)
        .lastWhere((m) => m.isUser, orElse: () => ChatMsg(isUser: true, text: ''))
        .text;
    try {
      await (_aiApiClient ??= AiApiClient()).sendFeedback(
        rating: rating,
        question: question,
        answer: msg.text,
        reason: reason,
        evidence: [
          for (final s in msg.sources)
            {
              'filename': s.regulation,
              'location': s.chapter,
              'chunk_id': s.chunkId,
              'document_id': s.documentId,
              'version_id': s.versionId,
              'page': s.page,
            },
        ],
      );
      if (!mounted) return;
      setState(() => msg.rating = rating);
      _saveToStore();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('의견을 보냈습니다. 감사합니다.')),
      );
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('의견을 보내지 못했습니다. 잠시 후 다시 시도해 주세요.')),
      );
    }
  }

  /// 👎 사유 입력. 취소하면 null, 비워 두고 보내면 ''.
  Future<String?> _askReason() {
    final controller = TextEditingController();
    return showDialog<String>(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        title: const Text('어떤 점이 틀렸나요?'),
        content: TextField(
          controller: controller,
          autofocus: true,
          maxLines: 3,
          maxLength: 2000,
          decoration: const InputDecoration(
            hintText: '예: 조항 번호가 다릅니다 (선택)',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogCtx),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(dialogCtx, controller.text),
            child: const Text('보내기'),
          ),
        ],
      ),
    ).whenComplete(controller.dispose);
  }

  void _appendErrorMessage(String message) {
    if (!mounted) {
      return;
    }
    setState(() {
      _messages.add(ChatMsg(isUser: false, text: message, isError: true));
    });
    _saveToStore();
  }

  void _saveToStore() {
    ConversationStore.instance.addOrUpdate(
      Conversation(
        id: widget.conversation.id,
        title: widget.conversation.title,
        createdAt: widget.conversation.createdAt,
        messages: List.of(_messages),
      ),
    );
  }

  ChatSource _sourceFrom(AiEvidenceSource source) {
    return ChatSource(
      regulation: source.fileName,
      chapter: source.linkedAnnex == null
          ? source.title
          : '${source.title} · ${source.linkedAnnex}',
      version: '',
      excerpt: _compactExcerpt(source.content),
      content: source.content,
      sourcePath: source.sourcePath,
      chunkId: source.chunkId,
      retriever: source.retriever,
      documentId: source.documentId,
      versionId: source.versionId,
      page: source.page,
    );
  }

  String? _compactExcerpt(String? content) {
    final text = content?.replaceAll(RegExp(r'\s+'), ' ').trim();
    if (text == null || text.isEmpty) {
      return null;
    }
    return text.length > 180 ? '${text.substring(0, 180)}…' : text;
  }

  @override
  Widget build(BuildContext context) {
    final itemCount = _messages.length + (_status != null ? 1 : 0);

    return Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(
        leading: const BackButton(),
        title: Text(
          widget.conversation.title,
          style: const TextStyle(fontSize: 16),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.more_horiz_rounded),
            onPressed: _showOptions,
          ),
        ],
      ),
      body: Column(
        children: [
          // Message list
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              itemCount: itemCount,
              itemBuilder: (context, i) {
                if (i == _messages.length) {
                  return _TypingIndicator(text: '${_status!}…');
                }
                final msg = _messages[i];
                return _MessageItem(
                  msg: msg,
                  onRate: (rating) => _rate(i, rating),
                  onOpenSource: (source) => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => RegulationViewerScreen(source: source),
                    ),
                  ),
                );
              },
            ),
          ),

          // Compose bar
          Container(
            width: double.infinity,
            color: AppColors.canvas,
            padding: const EdgeInsets.fromLTRB(16, 6, 16, 0),
            child: Text(
              'AI 답변은 참고용입니다. 공식 규정집이 우선합니다.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.secondaryInk, fontSize: 13),
            ),
          ),
          Container(
            decoration: BoxDecoration(
              color: AppColors.canvas,
              border: Border(top: BorderSide(color: AppColors.border)),
            ),
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  decoration: BoxDecoration(
                    color: AppColors.card,
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(color: AppColors.border),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.04),
                        blurRadius: 8,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      const SizedBox(width: 16),
                      Expanded(
                        child: TextField(
                          controller: _controller,
                          textInputAction: TextInputAction.send,
                          onSubmitted: (_) => _sendCurrentMessage(),
                          maxLines: 4,
                          minLines: 1,
                          decoration: InputDecoration(
                            hintText: '메시지 입력…',
                            hintStyle: TextStyle(
                              color: AppColors.ghostText,
                              fontSize: 14,
                            ),
                            border: InputBorder.none,
                            isDense: true,
                            contentPadding: EdgeInsets.symmetric(vertical: 14),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      GestureDetector(
                        onTap: _isSending ? null : _sendCurrentMessage,
                        behavior: HitTestBehavior.opaque,
                        child: Padding(
                          padding: const EdgeInsets.all(4),
                          child: Container(
                            width: 40,
                            height: 40,
                            decoration: BoxDecoration(
                              color: _isSending
                                  ? AppColors.border
                                  : AppColors.line6GoldDeep,
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(
                              Icons.arrow_upward_rounded,
                              color: Colors.white,
                              size: 20,
                              semanticLabel: '보내기',
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _TypingIndicator extends StatelessWidget {
  const _TypingIndicator({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 32,
          height: 32,
          margin: const EdgeInsets.only(right: 10, top: 2),
          decoration: const BoxDecoration(
            color: AppColors.line6GoldDeep,
            shape: BoxShape.circle,
          ),
          child: const Icon(
            Icons.smart_toy_outlined,
            color: Colors.white,
            size: 17,
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: AppColors.card,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: AppColors.border),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const SizedBox(
                width: 14,
                height: 14,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: AppColors.line6Gold,
                ),
              ),
              const SizedBox(width: 10),
              Flexible(
                child: Text(
                  text,
                  style: TextStyle(color: AppColors.secondaryInk, fontSize: 14),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _MessageItem extends StatelessWidget {
  const _MessageItem({
    required this.msg,
    required this.onOpenSource,
    required this.onRate,
  });
  final ChatMsg msg;
  final ValueChanged<ChatSource> onOpenSource;
  final ValueChanged<String> onRate;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: msg.isUser
          ? _UserBubble(text: msg.text)
          : _AiBubble(msg: msg, onOpenSource: onOpenSource, onRate: onRate),
    );
  }
}

class _UserBubble extends StatelessWidget {
  const _UserBubble({required this.text});
  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.end,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        const SizedBox(width: 48),
        Flexible(
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: const BoxDecoration(
              color: AppColors.line6GoldDeep,
              borderRadius: BorderRadius.only(
                topLeft: Radius.circular(18),
                topRight: Radius.circular(18),
                bottomLeft: Radius.circular(18),
                bottomRight: Radius.circular(4),
              ),
            ),
            child: Text(
              text,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 15,
                height: 1.45,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _AiBubble extends StatelessWidget {
  const _AiBubble({
    required this.msg,
    required this.onOpenSource,
    required this.onRate,
  });
  final ChatMsg msg;
  final ValueChanged<ChatSource> onOpenSource;
  final ValueChanged<String> onRate;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // AI avatar
        Container(
          width: 32,
          height: 32,
          margin: const EdgeInsets.only(right: 10, top: 2),
          decoration: const BoxDecoration(
            color: AppColors.line6GoldDeep,
            shape: BoxShape.circle,
          ),
          child: const Icon(
            Icons.smart_toy_outlined,
            color: Colors.white,
            size: 17,
          ),
        ),
        Flexible(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Message bubble
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 12,
                ),
                decoration: BoxDecoration(
                  color: AppColors.card,
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(4),
                    topRight: Radius.circular(18),
                    bottomLeft: Radius.circular(18),
                    bottomRight: Radius.circular(18),
                  ),
                  border: Border.all(color: AppColors.border),
                ),
                child: _buildMessageBody(msg.text),
              ),

              // Source cards: 여러 개면 가로로 넘겨 본다.
              if (msg.sources.length == 1) ...[
                const SizedBox(height: 8),
                _sourceCard(msg.sources.single),
              ] else if (msg.sources.length > 1) ...[
                const SizedBox(height: 8),
                Text(
                  '근거 ${msg.sources.length}건 · 옆으로 넘겨 보기',
                  style: TextStyle(color: AppColors.secondaryInk, fontSize: 13),
                ),
                const SizedBox(height: 6),
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      for (final source in msg.sources)
                        Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: SizedBox(width: 260, child: _sourceCard(source)),
                        ),
                    ],
                  ),
                ),
              ],
              if (!msg.isError) _feedbackRow(),
            ],
          ),
        ),
        const SizedBox(width: 40),
      ],
    );
  }

  Widget _feedbackRow() {
    Widget button(String rating, IconData icon, IconData selectedIcon, String tip) {
      final selected = msg.rating == rating;
      return IconButton(
        tooltip: tip,
        icon: Icon(
          selected ? selectedIcon : icon,
          size: 18,
          color: selected ? AppColors.line6Gold : AppColors.secondaryInk,
        ),
        // 한 번 평가하면 바꿀 수 없다(서버 기록과 화면이 어긋나지 않게).
        onPressed: msg.rating == null ? () => onRate(rating) : null,
      );
    }

    return Row(
      children: [
        button('up', Icons.thumb_up_outlined, Icons.thumb_up_rounded, '도움이 됐어요'),
        button('down', Icons.thumb_down_outlined, Icons.thumb_down_rounded, '틀렸거나 부족해요'),
      ],
    );
  }

  Widget _sourceCard(ChatSource source) => EvidenceSourceCard(
    regulation: source.regulation,
    chapter: source.chapter,
    excerpt: source.excerpt,
    related: source.isRelated,
    onOpenSource: () => onOpenSource(source),
  );

  Widget _buildMessageBody(String text) {
    // Render numbered lists with slight indentation, highlight quoted text
    final lines = text.split('\n');
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: lines.map((line) {
        if (line.startsWith('"') && line.endsWith('"')) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: HighlightText(line),
          );
        }
        return Text.rich(
          _boldSpans(line),
          style: TextStyle(color: AppColors.ink, fontSize: 15, height: 1.55),
        );
      }).toList(),
    );
  }

  // Markdown **bold**: odd segments after splitting on ** are bold.
  // ponytail: bold only; switch to flutter_markdown if headings/lists/links are needed.
  TextSpan _boldSpans(String line) {
    final parts = line.split('**');
    return TextSpan(
      children: [
        for (var i = 0; i < parts.length; i++)
          TextSpan(
            text: parts[i],
            style: i.isOdd ? const TextStyle(fontWeight: FontWeight.w700) : null,
          ),
      ],
    );
  }
}
