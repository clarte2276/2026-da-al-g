import 'package:flutter/material.dart';
import '../core/colors.dart';

class EvidenceMiniLabel extends StatelessWidget {
  const EvidenceMiniLabel({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(color: AppColors.softEvidence, borderRadius: BorderRadius.circular(8)),
      child: Text(
        '근거 원문 미리보기 포함',
        style: TextStyle(color: AppColors.evidence, fontSize: 12, fontWeight: FontWeight.w600),
      ),
    );
  }
}
