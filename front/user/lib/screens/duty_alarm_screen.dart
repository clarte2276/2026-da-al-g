import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../core/colors.dart';
import '../services/duty_alarm.dart';

class DutyAlarmScreen extends StatefulWidget {
  const DutyAlarmScreen({super.key});

  @override
  State<DutyAlarmScreen> createState() => _DutyAlarmScreenState();
}

class _DutyAlarmScreenState extends State<DutyAlarmScreen> {
  bool? _exactAllowed;
  final alarm = DutyAlarm.instance;

  @override
  void initState() {
    super.initState();
    unawaited(_refresh());
  }

  Future<void> _refresh() async {
    await alarm.recalculate();
    if (defaultTargetPlatform == TargetPlatform.android) {
      final allowed = await alarm.exactAlarmsAllowed();
      if (mounted) setState(() => _exactAllowed = allowed);
    }
  }

  Future<void> _toggle(DutyAlarmRule rule, bool value) async {
    await alarm.setRuleEnabled(rule, value);
    if (mounted && defaultTargetPlatform == TargetPlatform.android) {
      final allowed = await alarm.exactAlarmsAllowed();
      if (mounted) setState(() => _exactAllowed = allowed);
    }
  }

  Future<void> _showResult(
    Future<int> Function() action,
    String message,
  ) async {
    try {
      final count = await action();
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('$message $count개')));
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('근무 알림을 처리하지 못했어요: $error')));
      }
    }
  }

  String _date(DateTime date) =>
      '${date.month}월 ${date.day}일 ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('근무 알림')),
    body: ListenableBuilder(
      listenable: alarm,
      builder: (context, _) => ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
        children: [
          if (!alarm.supported)
            const _InfoCard(text: '근무 알림은 Android와 iOS에서 사용할 수 있어요.'),
          if (alarm.supported) ...[
            Card(
              color: AppColors.card,
              child: Column(
                children: [
                  for (final rule in DutyAlarmRule.values) _ruleRow(rule),
                  const Divider(height: 1),
                  SwitchListTile(
                    title: const Text('전날 21:00 근무 알림'),
                    subtitle: const Text('다음 날 출근 교번을 미리 알려요.'),
                    value: alarm.eveBefore,
                    onChanged: (value) async {
                      await alarm.setEveBefore(value);
                      if (mounted &&
                          defaultTargetPlatform == TargetPlatform.android) {
                        final allowed = await alarm.exactAlarmsAllowed();
                        if (mounted) setState(() => _exactAllowed = allowed);
                      }
                    },
                  ),
                ],
              ),
            ),
            if (defaultTargetPlatform == TargetPlatform.android &&
                _exactAllowed != true)
              Card(
                color: AppColors.card,
                child: ListTile(
                  leading: const Icon(
                    Icons.schedule_rounded,
                    color: AppColors.line6Gold,
                  ),
                  title: const Text('정확한 시각 알림 허용'),
                  subtitle: const Text('절전 중에도 예약한 시각에 맞춰 알려줘요.'),
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: () async {
                    final allowed = await alarm.openExactAlarmSettings();
                    if (mounted) setState(() => _exactAllowed = allowed);
                    await alarm.recalculate();
                  },
                ),
              ),
            if (defaultTargetPlatform == TargetPlatform.android &&
                alarm.fullScreenAllowed != true)
              Card(
                color: AppColors.card,
                child: ListTile(
                  leading: const Icon(
                    Icons.open_in_full_rounded,
                    color: AppColors.line6Gold,
                  ),
                  title: const Text('전체 화면 알림 허용'),
                  subtitle: const Text('알림 시 근무 알림을 화면에 표시해요.'),
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: alarm.openFullScreenSettings,
                ),
              ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: alarm.sendTestNotification,
                    icon: const Icon(Icons.notifications_active_outlined),
                    label: const Text('테스트 알림'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () =>
                        _showResult(alarm.recalculate, '근무표를 다시 계산했어요. 알림'),
                    icon: const Icon(Icons.refresh_rounded),
                    label: const Text('알림 다시 계산'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Text(
              '예정된 알림 · 30일',
              style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w700,
                color: AppColors.ink,
              ),
            ),
            const SizedBox(height: 8),
            Card(
              color: AppColors.card,
              child: alarm.upcoming.isEmpty
                  ? const Padding(
                      padding: EdgeInsets.all(20),
                      child: Center(child: Text('예정된 근무 알림이 없어요.')),
                    )
                  : Column(
                      children: [
                        for (final item in alarm.upcoming)
                          ListTile(
                            dense: true,
                            title: Text(item.title),
                            subtitle: Text(item.body),
                            trailing: Text(
                              _date(item.at),
                              style: TextStyle(color: AppColors.secondaryInk),
                            ),
                          ),
                      ],
                    ),
            ),
          ],
        ],
      ),
    ),
  );

  Widget _ruleRow(DutyAlarmRule rule) {
    final maxMinutes = rule == DutyAlarmRule.firstRunAfter ? 120 : 180;
    final choices =
        <int>{5, 10, 15, 20, 30, 40, 50, 60, 70, 90, 120, 150, 180}
            .where(
              (value) => value <= maxMinutes || value == alarm.minutes[rule],
            )
            .toList()
          ..sort();
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 8, 8),
          child: Row(
            children: [
              Expanded(
                child: Text(_title(rule), style: const TextStyle(fontSize: 15)),
              ),
              Switch(
                value: alarm.rules[rule]!,
                onChanged: (value) => _toggle(rule, value),
              ),
              const SizedBox(width: 4),
              DropdownButton<int>(
                value: alarm.minutes[rule],
                isDense: true,
                underline: const SizedBox.shrink(),
                items: [
                  for (final value in choices)
                    DropdownMenuItem(
                      value: value,
                      child: Text('$value분 ${_direction(rule)}'),
                    ),
                ],
                onChanged: (value) {
                  if (value != null) unawaited(alarm.setMinutes(rule, value));
                },
              ),
            ],
          ),
        ),
        if (rule != DutyAlarmRule.values.last)
          const Divider(height: 1, indent: 16, endIndent: 16),
      ],
    );
  }

  String _title(DutyAlarmRule rule) => switch (rule) {
    DutyAlarmRule.preparationBefore => '출근 준비 알림',
    DutyAlarmRule.firstRunAfter => '첫 운행 출장 알림',
    DutyAlarmRule.nextTrainSignatureBefore => '다음 열차 서명 알림',
    DutyAlarmRule.nextTrainDepartureBefore => '다음 열차 출장 알림',
    DutyAlarmRule.depotDepartureBefore => '출고 열차 알림',
  };

  String _direction(DutyAlarmRule rule) =>
      rule == DutyAlarmRule.firstRunAfter ? '후' : '전';
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({required this.text});
  final String text;

  @override
  Widget build(BuildContext context) => Card(
    color: AppColors.card,
    child: Padding(padding: const EdgeInsets.all(16), child: Text(text)),
  );
}
