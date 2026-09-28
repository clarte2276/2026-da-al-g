import 'package:flutter/material.dart';
import '../core/colors.dart';

class QuickActionGrid extends StatelessWidget {
  const QuickActionGrid({
    super.key,
    required this.onOpenSchedule,
    required this.onOpenBookmarks,
    required this.onOpenRegulations,
  });
  final VoidCallback onOpenSchedule, onOpenBookmarks, onOpenRegulations;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        _QuickTile(icon: Icons.calendar_month, label: '근무', onTap: onOpenSchedule),
        const SizedBox(width: 8),
        _QuickTile(icon: Icons.bookmark_border, label: '보관함', onTap: onOpenBookmarks),
        const SizedBox(width: 8),
        _QuickTile(icon: Icons.menu_book_rounded, label: '규정 본문', onTap: onOpenRegulations),
      ],
    );
  }
}

class _QuickTile extends StatelessWidget {
  const _QuickTile({required this.icon, required this.label, required this.onTap});
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(18),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 16),
          decoration: BoxDecoration(
            border: Border.all(color: AppColors.border),
            borderRadius: BorderRadius.circular(18),
            color: AppColors.card,
          ),
          child: Column(
            children: [
              Icon(icon, color: AppColors.line6Gold),
              const SizedBox(height: 10),
              Text(
                label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13, color: AppColors.ink),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
