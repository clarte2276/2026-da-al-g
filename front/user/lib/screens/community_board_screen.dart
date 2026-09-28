import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../widgets/app_card.dart';
import '../widgets/app_page.dart';

class CommunityBoardScreen extends StatelessWidget {
  const CommunityBoardScreen({super.key, required this.title});
  final String title;

  @override
  Widget build(BuildContext context) {
    final posts = _postsFor(title);
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: AppPage(
        children: [
          AppCard(
            padding: EdgeInsets.zero,
            child: Column(
              children: posts
                  .map((p) => ListTile(
                        title: Text(p.$1, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                        subtitle: Text(p.$2, style: TextStyle(fontSize: 12, color: AppColors.secondaryInk)),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.chat_bubble_outline_rounded, size: 13, color: AppColors.ghostText),
                            const SizedBox(width: 3),
                            Text('${p.$3}', style: TextStyle(fontSize: 12, color: AppColors.ghostText)),
                          ],
                        ),
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => _PostDetailScreen(post: p),
                          ),
                        ),
                      ))
                  .toList(),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('게시글 작성은 준비 중입니다.')),
        ),
        backgroundColor: AppColors.line6Gold,
        foregroundColor: Colors.white,
        child: const Icon(Icons.edit_rounded),
      ),
    );
  }

  static List<(String, String, int)> _postsFor(String board) {
    if (board == '질문게시판') {
      return [
        ('출입문 고장 시 승객 하차 절차 문의', '6호선 · 3시간 전', 5),
        ('교번 변경 신청 기준이 어떻게 되나요?', '6호선 · 어제', 2),
        ('열차 무선 주파수 확인 방법', '6호선 · 2일 전', 8),
      ];
    } else if (board == '비밀게시판') {
      return [
        ('비밀글입니다.', '6호선 · 1시간 전', 1),
        ('비밀글입니다.', '6호선 · 어제', 0),
      ];
    } else {
      return [
        ('오늘 응암 방면 6407 지연 있었네요', '6호선 · 30분 전', 3),
        ('신규 규정 2026.04 배포 확인하세요', '6호선 · 2시간 전', 7),
        ('휴게실 에어컨 드디어 고쳤습니다', '6호선 · 어제', 12),
        ('다음 달 교번표 나왔습니다', '6호선 · 2일 전', 4),
      ];
    }
  }
}

class _PostDetailScreen extends StatelessWidget {
  const _PostDetailScreen({required this.post});
  final (String, String, int) post;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('게시글')),
      body: AppPage(
        children: [
          Text(post.$1, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
          const SizedBox(height: 6),
          Text(post.$2, style: TextStyle(fontSize: 12, color: AppColors.secondaryInk)),
          const SizedBox(height: 16),
          Text(
            '게시글 본문입니다. (${post.$3}개의 답글이 있습니다.)',
            style: const TextStyle(fontSize: 14, height: 1.5),
          ),
        ],
      ),
    );
  }
}
