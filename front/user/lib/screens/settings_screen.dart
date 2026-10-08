import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../core/theme_controller.dart';
import '../services/duty_alarm.dart';
import '../widgets/app_card.dart';
import '../widgets/app_page.dart';
import '../widgets/page_header.dart';
import 'my_page_screen.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return AppPage(
      children: [
        const PageHeader(title: '설정'),
        // 노선은 마이페이지 정보 칸의 소속 노선이 대신한다.
        const MyPageSections(),
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
                        ButtonSegment(
                          value: ThemeMode.system,
                          label: Text('시스템'),
                        ),
                        ButtonSegment(
                          value: ThemeMode.light,
                          label: Text('라이트'),
                        ),
                        ButtonSegment(value: ThemeMode.dark, label: Text('다크')),
                      ],
                      selected: {ThemeController.instance.mode},
                      onSelectionChanged: (s) =>
                          ThemeController.instance.setMode(s.single),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
        const _DutyAlarmCard(),
      ],
    );
  }
}

/// 근무 알람: 출근 N분 전 + 전날 21:00 익일 근무 알림.
class _DutyAlarmCard extends StatelessWidget {
  const _DutyAlarmCard();

  @override
  Widget build(BuildContext context) {
    final alarm = DutyAlarm.instance;
    return AppCard(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      child: ListenableBuilder(
        listenable: alarm,
        builder: (context, _) => Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.alarm_rounded, color: AppColors.line6Gold),
                SizedBox(width: 16),
                Text('근무 알람', style: TextStyle(fontSize: 16)),
              ],
            ),
            if (!alarm.supported) ...[
              const SizedBox(height: 8),
              Text('이 기기에서는 알람을 지원하지 않습니다 (Android·iOS 전용).',
                  style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)),
            ] else ...[
              const SizedBox(height: 12),
              Text('출근 전 알림', style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)),
              const SizedBox(height: 6),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: [
                  ChoiceChip(
                    label: const Text('끔'),
                    selected: alarm.leadMinutes == null,
                    onSelected: (_) => alarm.setLeadMinutes(null),
                  ),
                  for (final m in DutyAlarm.leadChoices)
                    ChoiceChip(
                      label: Text('$m분 전'),
                      selected: alarm.leadMinutes == m,
                      onSelected: (_) => alarm.setLeadMinutes(m),
                    ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('익일 근무 알람', style: TextStyle(fontSize: 15)),
                        Text('전날 21:00 · 예) 내일 06:12 출근 · 5교번',
                            style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)),
                      ],
                    ),
                  ),
                  Switch(value: alarm.eveBefore, onChanged: alarm.setEveBefore),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
