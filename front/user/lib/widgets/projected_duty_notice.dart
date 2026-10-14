import 'package:flutter/material.dart';

import '../core/colors.dart';

class ProjectedDutyNotice extends StatelessWidget {
  const ProjectedDutyNotice({super.key, this.dark = false});

  final bool dark;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: dark
            ? Colors.white.withValues(alpha: 0.08)
            : AppColors.softEvidence,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.event_note_rounded, size: 18, color: AppColors.line6Gold),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '예상 근무',
                  style: TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 13,
                    color: dark ? Colors.white : AppColors.ink,
                  ),
                ),
                Text(
                  '실제 근무표가 아직 올라오지 않아 순환 교번으로 계산한 예상 근무입니다',
                  style: TextStyle(
                    fontSize: 12,
                    color: dark ? Colors.white70 : AppColors.secondaryInk,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
