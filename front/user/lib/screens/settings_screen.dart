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
              _SettingsTile(
                title: '규정 버전',
                value: '2026.04',
                icon: Icons.description_rounded,
              ),
            ],
          ),
        ),
        AppCard(
          padding: EdgeInsets.zero,
          child: AnimatedBuilder(
            animation: ThemeController.instance,
            builder: (context, _) => SwitchListTile(
              secondary: Icon(
                ThemeController.instance.isDark
                    ? Icons.dark_mode_rounded
                    : Icons.light_mode_rounded,
                color: AppColors.line6Gold,
              ),
              title: const Text('다크 모드'),
              subtitle: Text(
                ThemeController.instance.isDark ? '어두운 화면' : '밝은 화면',
                style: TextStyle(fontSize: 12, color: AppColors.secondaryInk),
              ),
              value: ThemeController.instance.isDark,
              activeThumbColor: AppColors.line6Gold,
              onChanged: (v) => ThemeController.instance.setDark(v),
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
