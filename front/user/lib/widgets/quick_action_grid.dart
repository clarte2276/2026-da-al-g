import 'package:flutter/material.dart';
import '../core/colors.dart';

class QuickActionGrid extends StatelessWidget {
  const QuickActionGrid({
    super.key,
    required this.onAskRegulation,
    required this.onOpenSchedule,
    this.onOpenBookmarks,
    this.onOpenRegulations,
    this.customLabels,
    this.customIcons,
  });
  final VoidCallback onAskRegulation, onOpenSchedule;
  final VoidCallback? onOpenBookmarks;

  /// 제공되면 두 번째 줄(규정 본문 + 플레이스홀더 2개)을 렌더링해 2×3 그리드가 된다.
  final VoidCallback? onOpenRegulations;
  final List<String>? customLabels;
  final List<IconData>? customIcons;

  @override
  Widget build(BuildContext context) {
    final firstRow = Row(
      children: [
        _QuickTile(icon: customIcons?[0] ?? Icons.search, label: customLabels?[0] ?? '규정검색', onTap: onAskRegulation),
        const SizedBox(width: 8),
        _QuickTile(icon: customIcons?[1] ?? Icons.calendar_month, label: customLabels?[1] ?? '시간표', onTap: onOpenSchedule),
        const SizedBox(width: 8),
        _QuickTile(
          icon: customIcons?[2] ?? Icons.bookmark_border,
          label: customLabels?[2] ?? '보관함',
          onTap: onOpenBookmarks ?? () {},
        ),
      ],
    );

    if (onOpenRegulations == null) {
      return firstRow;
    }

    return Column(
      children: [
        firstRow,
        const SizedBox(height: 8),
        Row(
          children: [
            _QuickTile(icon: Icons.menu_book_rounded, label: '규정 본문', onTap: onOpenRegulations!),
            const SizedBox(width: 8),
            const _QuickTile(icon: Icons.add_rounded, label: '준비 중', enabled: false),
            const SizedBox(width: 8),
            const _QuickTile(icon: Icons.add_rounded, label: '준비 중', enabled: false),
          ],
        ),
      ],
    );
  }
}

class _QuickTile extends StatelessWidget {
  const _QuickTile({required this.icon, required this.label, this.onTap, this.enabled = true});
  final IconData icon;
  final String label;
  final VoidCallback? onTap;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    final accent = enabled ? AppColors.line6Gold : AppColors.ghostText;
    final textColor = enabled ? AppColors.ink : AppColors.ghostText;
    return Expanded(
      child: InkWell(
        onTap: enabled ? onTap : null,
        borderRadius: BorderRadius.circular(18),
        child: Opacity(
          opacity: enabled ? 1 : 0.55,
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              border: Border.all(color: AppColors.border),
              borderRadius: BorderRadius.circular(18),
              color: AppColors.card,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(icon, color: accent),
                const SizedBox(height: 12),
                Text(label, style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: textColor)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
