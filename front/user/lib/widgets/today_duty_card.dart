import 'package:flutter/material.dart';
import '../core/colors.dart';
import 'status_pill.dart';

class TodayDutyCard extends StatelessWidget {
  const TodayDutyCard({super.key, this.isHeader = false, this.onTap});
  final bool isHeader;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: AppColors.dutyCardBg,
          borderRadius: BorderRadius.circular(18),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const StatusPill(label: '오늘 근무', color: Colors.white, bgColor: Color(0xff3d3d3d)),
                const SizedBox(width: 8),
                const StatusPill(label: 'D-0', color: AppColors.line6Gold),
                const Spacer(),
                if (!isHeader) const Icon(Icons.arrow_forward_ios_rounded, size: 14, color: Colors.white54),
              ],
            ),
            const SizedBox(height: 20),
            const Text(
              '출무 14:20 · 응암 → 신내',
              style: TextStyle(color: Colors.white, fontSize: 19, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            Text(
              '열차 6407 · 첫 출발 14:47 · 휴게 18:10',
              style: TextStyle(color: AppColors.dutyMeta, fontSize: 14),
            ),
            const SizedBox(height: 16),
            Container(
              height: 4,
              width: double.infinity,
              decoration: BoxDecoration(color: AppColors.line6Gold, borderRadius: BorderRadius.circular(2)),
            ),
          ],
        ),
      ),
    );
  }
}
