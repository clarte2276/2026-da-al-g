import 'dart:async';

import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../data/conversation_store.dart';
import '../data/mock_conversations.dart';
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
    });
    _scrollAfterBuild();

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
      final response = await (_aiApiClient ??= AiApiClient()).ask(
        question,
        history: history,
      );
      if (!mounted) {
        return;
      }

      setState(() {
        _messages.add(
          ChatMsg(
            isUser: false,
            text: response.answer.isEmpty
                ? '제공된 문서에서 확인되지 않습니다.'
                : response.answer,
            source: _sourceFrom(response.sources),
          ),
        );
      });
      _saveToStore();
    } on TimeoutException {
      _appendErrorMessage(
        'FastAPI 서버 응답 시간이 초과되었습니다.\n\n백엔드와 AI DB 연결 상태를 확인한 뒤 다시 시도해주세요.',
      );
    } on AiApiException catch (error) {
      _appendErrorMessage('FastAPI 응답을 가져오지 못했습니다.\n\n${error.message}');
    } catch (error) {
      _appendErrorMessage('AI 서버에 연결하지 못했습니다.\n\n$error');
    } finally {
      if (mounted) {
        setState(() {
          _isSending = false;
        });
        _scrollAfterBuild();
      }
    }
  }

  void _appendErrorMessage(String message) {
    if (!mounted) {
      return;
    }
    setState(() {
      _messages.add(ChatMsg(isUser: false, text: message));
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

  ChatSource? _sourceFrom(List<AiEvidenceSource> sources) {
    if (sources.isEmpty) {
      return null;
    }

    final source = sources.first;
    return ChatSource(
      regulation: source.fileName,
      chapter: source.linkedAnnex == null
          ? source.title
          : '${source.title} · ${source.linkedAnnex}',
      version: '원문 기준',
      excerpt: _compactExcerpt(source.content),
      content: source.content,
      sourcePath: source.sourcePath,
      chunkId: source.chunkId,
      retriever: source.retriever,
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
    final itemCount = _messages.length + (_isSending ? 1 : 0);

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
                  return const _TypingIndicator(text: '답변 생성 중...');
                }
                final msg = _messages[i];
                return _MessageItem(
                  msg: msg,
                  onOpenSource: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) =>
                          RegulationViewerScreen(source: msg.source),
                    ),
                  ),
                );
              },
            ),
          ),

          // Compose bar
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
                      Padding(
                        padding: const EdgeInsets.only(bottom: 6, right: 6),
                        child: GestureDetector(
                          onTap: _isSending ? null : _sendCurrentMessage,
                          child: Container(
                            width: 34,
                            height: 34,
                            decoration: BoxDecoration(
                              color: _isSending
                                  ? AppColors.border
                                  : AppColors.line6Gold,
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(
                              Icons.arrow_upward_rounded,
                              color: Colors.white,
                              size: 18,
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
            color: AppColors.line6Gold,
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
  const _MessageItem({required this.msg, required this.onOpenSource});
  final ChatMsg msg;
  final VoidCallback onOpenSource;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: msg.isUser
          ? _UserBubble(text: msg.text)
          : _AiBubble(msg: msg, onOpenSource: onOpenSource),
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
              color: AppColors.line6Gold,
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
  const _AiBubble({required this.msg, required this.onOpenSource});
  final ChatMsg msg;
  final VoidCallback onOpenSource;

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
            color: AppColors.line6Gold,
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

              // Source card
              if (msg.source != null) ...[
                const SizedBox(height: 8),
                EvidenceSourceCard(
                  regulation: msg.source!.regulation,
                  chapter: msg.source!.chapter,
                  version: msg.source!.version,
                  excerpt: msg.source!.excerpt,
                  onOpenSource: onOpenSource,
                ),
              ],
            ],
          ),
        ),
        const SizedBox(width: 40),
      ],
    );
  }

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
        return Text(
          line,
          style: TextStyle(color: AppColors.ink, fontSize: 15, height: 1.55),
        );
      }).toList(),
    );
  }
}
