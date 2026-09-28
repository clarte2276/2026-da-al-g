import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../widgets/app_card.dart';
import '../widgets/app_page.dart';
import '../widgets/page_header.dart';

class FAQScreen extends StatelessWidget {
  const FAQScreen({super.key});

  @override
  Widget build(BuildContext context) {
    const items = [
      ('규정 버전은 어떻게 확인하나요?', '설정 → 규정 버전에서 현재 적용 중인 버전을 확인할 수 있습니다. 최신 버전은 2026.04입니다.'),
      ('근무표 엑셀 파일은 어떤 형식이어야 하나요?', '6호선 승무 표준 양식(.xlsx)을 지원합니다. 교번·출무시각·열차번호 열이 포함된 형식이어야 합니다.'),
      ('AI 도우미 답변의 근거 조항을 직접 확인하려면?', '채팅방에서 답변 아래 파란색 EvidenceCard의 "원문 보기"를 탭하면 해당 규정 조항으로 이동합니다.'),
      ('보관함에 조항을 추가하려면?', '규정 원문 화면에서 북마크 아이콘을 탭하면 보관함에 저장됩니다.'),
      ('크루룸 채팅은 어떻게 참여하나요?', '채팅 탭 → 6호선 크루룸을 탭하면 참여할 수 있습니다.'),
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('자주 묻는 질문')),
      body: AppPage(
        children: [
          const PageHeader(title: 'FAQ', eyebrow: '자주 묻는 질문'),
          ...items.map((item) => _FaqItem(question: item.$1, answer: item.$2)),
        ],
      ),
    );
  }
}

class _FaqItem extends StatefulWidget {
  const _FaqItem({required this.question, required this.answer});
  final String question, answer;

  @override
  State<_FaqItem> createState() => _FaqItemState();
}

class _FaqItemState extends State<_FaqItem> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      padding: EdgeInsets.zero,
      child: InkWell(
        onTap: () => setState(() => _expanded = !_expanded),
        borderRadius: BorderRadius.circular(18),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Text('Q', style: TextStyle(color: AppColors.line6Gold, fontWeight: FontWeight.w900, fontSize: 15)),
                  const SizedBox(width: 10),
                  Expanded(child: Text(widget.question, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14))),
                  Icon(_expanded ? Icons.expand_less_rounded : Icons.expand_more_rounded, color: AppColors.ghostText),
                ],
              ),
              if (_expanded) ...[
                const SizedBox(height: 12),
                const Divider(height: 1),
                const SizedBox(height: 12),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('A', style: TextStyle(color: AppColors.evidence, fontWeight: FontWeight.w900, fontSize: 15)),
                    const SizedBox(width: 10),
                    Expanded(child: Text(widget.answer, style: TextStyle(fontSize: 13, height: 1.5, color: AppColors.secondaryInk))),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
