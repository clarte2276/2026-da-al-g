import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../data/conversation_store.dart';
import '../data/mock_conversations.dart';
import '../widgets/chat_input_bar.dart';
import 'chat_room_screen.dart';
import 'regulation_library_screen.dart';

class ChatListScreen extends StatefulWidget {
  const ChatListScreen({super.key});

  @override
  State<ChatListScreen> createState() => _ChatListScreenState();
}

class _ChatListScreenState extends State<ChatListScreen> {
  final _focusNode = FocusNode();

  @override
  void dispose() {
    _focusNode.dispose();
    super.dispose();
  }

  Future<void> _startNew(String text) async {
    final conv = newConversationFrom(text);
    ConversationStore.instance.addOrUpdate(conv);
    await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => ChatRoomScreen(conversation: conv)),
    );
    if (mounted) setState(() {});
  }

  Future<void> _openConversation(Conversation conv) async {
    await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => ChatRoomScreen(conversation: conv)),
    );
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.canvas,
      body: Column(
        children: [
          // Header
          Container(
            color: AppColors.card,
            padding: const EdgeInsets.fromLTRB(20, 16, 12, 14),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        '규정 AI 도우미',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      SizedBox(height: 2),
                      Text(
                        '운전취급·복무·안전관리 규정 검색',
                        style: TextStyle(
                          fontSize: 12,
                          color: AppColors.secondaryInk,
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(
                    Icons.menu_book_rounded,
                    color: AppColors.line6Gold,
                  ),
                  tooltip: '규정 본문',
                  onPressed: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => const RegulationLibraryScreen(),
                    ),
                  ),
                ),
                IconButton(
                  icon: const Icon(
                    Icons.edit_square,
                    color: AppColors.line6Gold,
                  ),
                  tooltip: '새 대화',
                  onPressed: () => _focusNode.requestFocus(),
                ),
              ],
            ),
          ),
          const Divider(height: 1),

          // Conversation list
          Expanded(
            child: Builder(
              builder: (context) {
                final convs = ConversationStore.instance.conversations;
                if (convs.isEmpty) {
                  return const _EmptyChatList();
                }
                return ListView.separated(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  itemCount: convs.length,
                  separatorBuilder: (context, index) =>
                      const Divider(height: 1, indent: 56),
                  itemBuilder: (context, i) => _ConversationTile(
                    conversation: convs[i],
                    onTap: () => _openConversation(convs[i]),
                  ),
                );
              },
            ),
          ),

          // Bottom compose bar (shared widget)
          ChatInputBar(focusNode: _focusNode, onSubmit: _startNew),
        ],
      ),
    );
  }
}

class _EmptyChatList extends StatelessWidget {
  const _EmptyChatList();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.chat_bubble_outline_rounded,
              size: 48,
              color: AppColors.ghostText,
            ),
            const SizedBox(height: 12),
            const Text(
              '아직 대화가 없어요.\n아래 입력창에 질문해보세요.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 6),
            Text(
              '예: "출입문 고장 시 승객 하차 절차"',
              style: TextStyle(fontSize: 12, color: AppColors.secondaryInk),
            ),
          ],
        ),
      ),
    );
  }
}

class _ConversationTile extends StatelessWidget {
  const _ConversationTile({required this.conversation, required this.onTap});
  final Conversation conversation;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: AppColors.softEvidence,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(
                Icons.chat_bubble_outline_rounded,
                color: AppColors.evidence,
                size: 16,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          conversation.title,
                          style: const TextStyle(
                            fontWeight: FontWeight.w600,
                            fontSize: 14,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        conversation.timeAgo,
                        style: TextStyle(
                          fontSize: 11,
                          color: AppColors.ghostText,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 3),
                  Text(
                    conversation.preview,
                    style: TextStyle(
                      fontSize: 12,
                      color: AppColors.secondaryInk,
                      height: 1.3,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
