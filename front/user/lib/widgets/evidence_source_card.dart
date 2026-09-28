import 'package:flutter/material.dart';
import '../core/colors.dart';
import 'app_card.dart';

class EvidenceSourceCard extends StatelessWidget {
  const EvidenceSourceCard({
    super.key,
    required this.regulation,
    required this.chapter,
    required this.version,
    required this.onOpenSource,
    this.excerpt,
  });
  final String regulation, chapter, version;
  final String? excerpt;
  final VoidCallback onOpenSource;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      background: AppColors.softEvidence,
      borderColor: AppColors.evidence,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.verified_rounded, color: AppColors.evidence, size: 18),
              SizedBox(width: 8),
              Text(
                '근거 확인됨',
                style: TextStyle(
                  color: AppColors.evidence,
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
            '$chapter · $version',
            style: TextStyle(color: AppColors.secondaryInk, fontSize: 13),
          ),
          if (excerpt != null && excerpt!.trim().isNotEmpty) ...[
            const SizedBox(height: 10),
            Text(
              excerpt!,
              style: TextStyle(
                color: AppColors.secondaryInk,
                fontSize: 12,
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
                foregroundColor: AppColors.evidence,
                side: BorderSide(color: AppColors.evidence),
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
