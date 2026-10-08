import 'package:flutter/material.dart';
import '../core/colors.dart';

/// 서버에 닿지 못해 기기에 저장된 근무표를 보여줄 때의 안내.
class OfflineBanner extends StatelessWidget {
  const OfflineBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.line6.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(children: [
        const Icon(Icons.cloud_off_rounded, size: 18, color: AppColors.line6),
        const SizedBox(width: 8),
        Expanded(
          child: Text('오프라인 상태예요 — 저장된 근무표를 보여드려요',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.ink)),
        ),
      ]),
    );
  }
}
