import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../data/chat_models.dart';
import '../data/conversation_store.dart';
import '../widgets/app_card.dart';
import '../widgets/app_page.dart';
import '../widgets/page_header.dart';
import 'chat_room_screen.dart';

class BookmarkScreen extends StatefulWidget {
  const BookmarkScreen({super.key});

  @override
  State<BookmarkScreen> createState() => _BookmarkScreenState();
}

class _BookmarkScreenState extends State<BookmarkScreen> {
  void _remove(Conversation conversation) {
    ConversationStore.instance.addOrUpdate(
      Conversation(
        id: conversation.id,
        title: conversation.title,
        createdAt: conversation.createdAt,
        messages: conversation.messages,
        saved: false,
      ),
    );
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final conversations = ConversationStore.instance.conversations
        .where((conversation) => conversation.saved)
        .toList();

    return Scaffold(
      appBar: AppBar(title: const Text('보관함')),
      body: AppPage(
        children: [
          const PageHeader(title: '보관함', eyebrow: '저장한 채팅'),
          if (conversations.isEmpty)
            const _EmptyState()
          else
            AppCard(
              padding: EdgeInsets.zero,
              child: Column(
                children: [
                  for (final entry in conversations.asMap().entries) ...[
                    if (entry.key > 0)
                      const Divider(height: 1, indent: 56),
                    Material(
                      type: MaterialType.transparency,
                      child: ListTile(
                        leading: const Icon(
                          Icons.bookmark_rounded,
                          color: AppColors.line6Gold,
                        ),
                        title: Text(
                          entry.value.title,
                          style: const TextStyle(
                            fontWeight: FontWeight.w700,
                            fontSize: 14,
                          ),
                        ),
                        subtitle: Text(
                          entry.value.preview,
                          style: const TextStyle(fontSize: 13),
                        ),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              entry.value.timeAgo,
                              style: TextStyle(
                                color: AppColors.ghostText,
                                fontSize: 13,
                              ),
                            ),
                            IconButton(
                              tooltip: '보관함에서 제거',
                              icon: Icon(
                                Icons.close_rounded,
                                size: 18,
                                color: AppColors.ghostText,
                              ),
                              onPressed: () => _remove(entry.value),
                            ),
                          ],
                        ),
                        onTap: () async {
                          await Navigator.push<void>(
                            context,
                            MaterialPageRoute(
                              builder: (_) => ChatRoomScreen(
                                conversation: entry.value,
                              ),
                            ),
                          );
                          if (mounted) setState(() {});
                        },
                      ),
                    ),
                  ],
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 80),
      child: Column(
        children: [
          Icon(
            Icons.bookmark_border_rounded,
            size: 56,
            color: AppColors.ghostText,
          ),
          const SizedBox(height: 12),
          const Text(
            '저장된 채팅이 없습니다',
            style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
          ),
          const SizedBox(height: 6),
          Text(
            '채팅 화면에서 북마크 아이콘을 탭하면\n여기에 저장됩니다.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: AppColors.secondaryInk,
              fontSize: 13,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }
}
