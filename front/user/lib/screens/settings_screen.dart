import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../core/theme_controller.dart';
import '../widgets/app_card.dart';
import '../widgets/app_page.dart';
import '../widgets/page_header.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return AppPage(
      children: [
        const PageHeader(title: '설정'),
        AppCard(
          padding: EdgeInsets.zero,
          child: const Column(
            children: [
              _SettingsTile(
                title: '노선',
                value: '서울메트로 6호선',
                icon: Icons.train_rounded,
              ),
            ],
          ),
        ),
        AppCard(
          padding: EdgeInsets.zero,
          child: AnimatedBuilder(
            animation: ThemeController.instance,
            builder: (context, _) => Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        ThemeController.instance.isDark
                            ? Icons.dark_mode_rounded
                            : Icons.light_mode_rounded,
                        color: AppColors.line6Gold,
                      ),
                      const SizedBox(width: 16),
                      const Text('화면 모드', style: TextStyle(fontSize: 16)),
                    ],
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: SegmentedButton<ThemeMode>(
                      segments: const [
                        ButtonSegment(value: ThemeMode.system, label: Text('시스템')),
                        ButtonSegment(value: ThemeMode.light, label: Text('라이트')),
                        ButtonSegment(value: ThemeMode.dark, label: Text('다크')),
                      ],
                      selected: {ThemeController.instance.mode},
                      onSelectionChanged: (s) => ThemeController.instance.setMode(s.single),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _SettingsTile extends StatelessWidget {
  const _SettingsTile({
    required this.title,
    required this.value,
    required this.icon,
  });
  final String title, value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: AppColors.line6Gold),
      title: Text(title),
      trailing: Text(
        value,
        style: TextStyle(
          fontWeight: FontWeight.w700,
          color: AppColors.secondaryInk,
        ),
      ),
    );
  }
}
