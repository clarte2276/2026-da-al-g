import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../core/models/rag_models.dart';
import '../core/services/rag_api_client.dart';
import '../widgets/chat_message_bubble.dart';
import '../widgets/connection_status_card.dart';
import '../widgets/message_composer.dart';

class ChatPage extends StatefulWidget {
  const ChatPage({
    super.key,
    this.api,
    this.user,
    this.onLogout,
    this.onSessionExpired,
  });

  final RagApiClient? api;
  final AuthUser? user;
  final VoidCallback? onLogout;
  final VoidCallback? onSessionExpired;

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  static const _fallbackSuggestions = [
    '출입문 고장으로 전체 출입문이 열리지 않을 때 어떻게 조치해야 하나요?',
    '차량고장으로 자력운전이 곤란하면 어떻게 해야 하나요?',
    '제동관 또는 공기관 고장으로 통기불능일 때 어떻게 조치하나요?',
  ];

  late final RagApiClient _api = widget.api ?? RagApiClient();
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  final _messages = <ChatMessage>[
    const ChatMessage(
      isUser: false,
      text:
          '안녕하세요. 철도 업무 문서나 일반적인 내용을 질문해 주세요.\n\n문서 질문에는 검색된 원문 근거를 함께 보여드립니다.',
    ),
  ];
  var _suggestions = _fallbackSuggestions;
  bool _loading = false;
  bool _checkingConnection = false;
  String? _embeddingProvider;
  String? _connectionError;

  @override
  void initState() {
    super.initState();
    unawaited(_loadSuggestions());
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _loadSuggestions() async {
    try {
      final raw = await rootBundle.loadString(
        'assets/data/suggested_questions.json',
      );
      final decoded = jsonDecode(raw);
      if (!mounted || decoded is! List) return;
      final loaded = decoded
          .whereType<String>()
          .where((item) => item.trim().isNotEmpty)
          .toList();
      if (loaded.isNotEmpty) setState(() => _suggestions = loaded);
    } catch (_) {
      // The in-code defaults keep the first screen usable if the asset is unavailable.
    }
  }

  Future<void> _checkConnection() async {
    if (_checkingConnection) return;
    setState(() {
      _checkingConnection = true;
      _connectionError = null;
    });
    try {
      final provider = await _api.health();
      if (!mounted) return;
      setState(() {
        _embeddingProvider = provider;
        _checkingConnection = false;
      });
    } catch (error) {
      if (!mounted) return;
      if (error is RagApiException && error.statusCode == 401) {
        widget.onSessionExpired?.call();
        return;
      }
      setState(() {
        _checkingConnection = false;
        _connectionError = _errorMessage(error);
      });
    }
  }

  Future<void> _send([String? preset]) async {
    if (_loading) return;
    final question = (preset ?? _controller.text).trim();
    if (question.isEmpty) return;

    final history = _messages
        .where((item) => !item.isError)
        .toList()
        .reversed
        .take(8)
        .toList()
        .reversed
        .map(
          (item) => <String, String>{
            'role': item.isUser ? 'user' : 'assistant',
            'content': item.text,
          },
        )
        .toList();
    _controller.clear();
    setState(() {
      _messages.add(ChatMessage(isUser: true, text: question));
      _loading = true;
      _connectionError = null;
    });
    _scrollToEnd();

    try {
      final response = await _api.ask(question, history: history);
      if (!mounted) return;
      setState(() {
        _messages.add(
          ChatMessage(isUser: false, text: response.answer, response: response),
        );
        _embeddingProvider = response.embeddingProvider;
        _loading = false;
      });
    } catch (error) {
      if (!mounted) return;
      if (error is RagApiException && error.statusCode == 401) {
        widget.onSessionExpired?.call();
        return;
      }
      final message = _errorMessage(error);
      setState(() {
        _messages.add(
          ChatMessage(
            isUser: false,
            isError: true,
            text: '채팅 API에 연결하지 못했습니다.\n$message',
          ),
        );
        _loading = false;
        _connectionError = message;
      });
    }
    _scrollToEnd();
  }

  String _errorMessage(Object error) {
    if (error is RagApiException) return error.message;
    return error.toString().replaceFirst('Exception: ', '');
  }

  void _scrollToEnd() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.auto_awesome_rounded),
            SizedBox(width: 10),
            Text('Da-Al-G AI'),
          ],
        ),
        actions: [
          if (widget.user != null)
            IconButton(
              onPressed: widget.onLogout,
              tooltip: '로그아웃',
              icon: const Icon(Icons.logout_rounded),
            ),
          IconButton(
            onPressed: _checkConnection,
            tooltip: '백엔드 연결 확인',
            icon: const Icon(Icons.sync_rounded),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 900),
            child: Column(
              children: [
                ConnectionStatusCard(
                  baseUrl: _api.baseUrl,
                  provider: _embeddingProvider,
                  checking: _checkingConnection,
                  error: _connectionError,
                  onCheck: _checkConnection,
                ),
                Expanded(child: _buildMessages(context)),
                MessageComposer(
                  controller: _controller,
                  loading: _loading,
                  onSend: _send,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMessages(BuildContext context) {
    final itemCount = _messages.length + (_loading ? 1 : 0);
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 20),
      itemCount: itemCount,
      itemBuilder: (context, index) {
        if (_loading && index == itemCount - 1) return const LoadingBubble();
        final message = _messages[index];
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ChatMessageBubble(message: message, api: _api),
            if (_messages.length == 1 && index == 0 && !_loading)
              _buildSuggestions(context),
          ],
        );
      },
    );
  }

  Widget _buildSuggestions(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Wrap(
        spacing: 8,
        runSpacing: 8,
        children: _suggestions
            .map(
              (question) => ActionChip(
                label: Text(question),
                onPressed: () => _send(question),
              ),
            )
            .toList(),
      ),
    );
  }
}
