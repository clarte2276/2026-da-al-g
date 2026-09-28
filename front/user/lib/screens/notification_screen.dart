import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../widgets/app_card.dart';
import '../widgets/app_page.dart';
import '../widgets/page_header.dart';

class NotificationScreen extends StatelessWidget {
  const NotificationScreen({super.key});

  @override
  Widget build(BuildContext context) {
    const items = [
      (Icons.campaign_rounded, '공지', '운전취급규정 2026.04 버전이 배포되었습니다.', '방금 전'),
      (Icons.schedule_rounded, '근무', '내일 06:10 출무 예정입니다.', '1시간 전'),
      (Icons.question_answer_rounded, '커뮤니티', '내 질문에 새 답변이 달렸습니다.', '3시간 전'),
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('알림')),
      body: AppPage(
        children: [
          const PageHeader(title: '알림'),
          AppCard(
            padding: EdgeInsets.zero,
            child: Column(
              children: items
                  .map((item) => ListTile(
                        leading: CircleAvatar(
                          backgroundColor: AppColors.softEvidence,
                          child: Icon(item.$1, color: AppColors.evidence, size: 20),
                        ),
                        title: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              margin: const EdgeInsets.only(right: 6),
                              decoration: BoxDecoration(
                                color: AppColors.line6Gold.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(item.$2, style: const TextStyle(fontSize: 11, color: AppColors.line6Gold, fontWeight: FontWeight.w700)),
                            ),
                            Text(item.$4, style: TextStyle(fontSize: 11, color: AppColors.ghostText)),
                          ],
                        ),
                        subtitle: Text(item.$3, style: const TextStyle(fontSize: 13)),
                        onTap: () => _showComingSoon(context),
                      ))
                  .toList(),
            ),
          ),
        ],
      ),
    );
  }

  void _showComingSoon(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('준비 중입니다.')),
    );
  }
}
