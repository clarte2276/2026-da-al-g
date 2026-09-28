import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../widgets/app_card.dart';
import '../widgets/app_page.dart';
import '../widgets/board_header.dart';
import '../widgets/page_header.dart';
import '../widgets/quick_action_grid.dart';

class CommunityListScreen extends StatelessWidget {
  const CommunityListScreen({
    super.key,
    required this.onOpenBoard,
    required this.onOpenFAQ,
    required this.onOpenBookmarks,
  });
  final Function(String) onOpenBoard;
  final VoidCallback onOpenFAQ;
  final VoidCallback onOpenBookmarks;

  @override
  Widget build(BuildContext context) {
    return AppPage(
      children: [
        const PageHeader(title: '커뮤니티', eyebrow: '승무원 지식 공유'),
        QuickActionGrid(
          onAskRegulation: onOpenFAQ,
          onOpenSchedule: () => onOpenBoard('자유게시판'),
          onOpenBookmarks: onOpenBookmarks,
          customLabels: const ['자주 묻는 질문', '자유게시판', '보관함'],
          customIcons: const [Icons.help_outline_rounded, Icons.forum_outlined, Icons.bookmark_border_rounded],
        ),
        AppCard(
          padding: EdgeInsets.zero,
          child: Column(
            children: [
              const BoardHeader(title: '게시판 목록', action: ''),
              _BoardItem(title: '자유게시판', icon: Icons.chat_bubble_outline_rounded, onTap: () => onOpenBoard('자유게시판')),
              _BoardItem(title: '질문게시판', icon: Icons.question_answer_outlined, onTap: () => onOpenBoard('질문게시판')),
              _BoardItem(title: '비밀게시판', icon: Icons.lock_outline_rounded, onTap: () => onOpenBoard('비밀게시판')),
            ],
          ),
        ),
      ],
    );
  }
}

class _BoardItem extends StatelessWidget {
  const _BoardItem({required this.title, required this.icon, required this.onTap});
  final String title;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: AppColors.line6Gold),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
      trailing: const Icon(Icons.chevron_right_rounded),
      onTap: onTap,
    );
  }
}
