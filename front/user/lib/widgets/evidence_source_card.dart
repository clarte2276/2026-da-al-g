import 'package:flutter/material.dart';
import '../core/colors.dart';
import 'app_card.dart';

class EvidenceSourceCard extends StatelessWidget {
  const EvidenceSourceCard({
    super.key,
    required this.regulation,
    required this.chapter,
    required this.onOpenSource,
    this.excerpt,
    this.related = false,
  });
  final String regulation, chapter;
  final String? excerpt;

  /// 그래프로 간접 연결된 근거면 '관련 조항'으로 약하게 표시한다.
  final bool related;
  final VoidCallback onOpenSource;

  @override
  Widget build(BuildContext context) {
    final accent = related ? AppColors.secondaryInk : AppColors.evidence;
    return AppCard(
      background: AppColors.softEvidence,
      borderColor: related ? AppColors.border : AppColors.evidence,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                related ? Icons.link_rounded : Icons.description_outlined,
                color: accent,
                size: 18,
              ),
              const SizedBox(width: 8),
              Text(
                related ? '관련 조항' : '근거',
                style: TextStyle(
                  color: accent,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            regulation,
            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
          ),
          const SizedBox(height: 4),
          Text(
            chapter,
            style: TextStyle(color: AppColors.secondaryInk, fontSize: 13),
          ),
          if (excerpt != null && excerpt!.trim().isNotEmpty) ...[
            const SizedBox(height: 10),
            Text(
              excerpt!,
              style: TextStyle(
                color: AppColors.secondaryInk,
                fontSize: 13,
                height: 1.45,
              ),
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
          ],
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: onOpenSource,
              style: OutlinedButton.styleFrom(
                foregroundColor: accent,
                side: BorderSide(color: accent),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text('원문 보기'),
            ),
          ),
        ],
      ),
    );
  }
}
