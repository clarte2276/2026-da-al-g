import 'package:flutter/material.dart';
import '../core/colors.dart';

class PageHeader extends StatelessWidget {
  const PageHeader({super.key, required this.title, this.eyebrow});
  final String title;
  final String? eyebrow;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (eyebrow != null)
          Text(
            eyebrow!,
            style: TextStyle(color: AppColors.secondaryInk, fontSize: 13),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        Text(
          title,
          style: TextStyle(
            fontSize: 28,
            fontWeight: FontWeight.w800,
            color: AppColors.ink,
          ),
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
      ],
    );
  }
}
