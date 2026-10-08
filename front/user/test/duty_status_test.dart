import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:user/core/duty_data.dart';
import 'package:user/widgets/today_duty_card.dart';

DutyMonth _month() => DutyMonth.fromJson({
      'month': '2026-10',
      'dates': ['2026-10-01', '2026-10-02', '2026-10-03', '2026-10-04'],
      'drivers': [
        {
          'no': 1,
          'name': '가동훈',
          'empNo': '21714093',
          'days': {
            '2026-10-01': {'code': '70', 'type': 'night', 'turn': '70', 'dayType': '평', 'turnKey': '평평:70'},
            '2026-10-02': {'code': '70~', 'type': 'off', 'turn': null, 'dayType': '평', 'continues': '평평:70'},
            '2026-10-03': {'code': '휴19', 'type': 'rest', 'turn': null, 'dayType': '휴'},
            // 옛 데이터: turnKey 없음 → 교번 id로 찾는다.
            '2026-10-04': {'code': '5', 'type': 'day', 'turn': '5'},
          },
        },
      ],
      'turns': {
        '평평:70': {
          'id': '70',
          'type': 'night',
          'dayType': '평평',
          'depart': '18:30',
          'arrive': '07:10',
          'nextDay': true,
          'break': '23:00',
          'segments': [
            {'kind': 'run', 'train': '6256', 'from': '응암', 'to': '봉화산', 'dep': '19:00', 'arr': '20:16', 'dir': 'up'},
            {'kind': 'standby', 'train': '', 'from': '신내기지', 'to': '신내기지', 'dep': '23:00', 'arr': '05:00'},
            {'kind': 'run', 'train': '6271', 'from': '봉화산', 'to': '응암', 'dep': '05:10', 'arr': '06:26', 'dir': 'down', 'nextDay': true},
          ],
        },
        '휴휴:70': {'id': '70', 'type': 'night', 'depart': '19:00', 'arrive': '07:30', 'nextDay': true},
        '5': {'id': '5', 'type': 'day', 'depart': '08:35', 'arrive': '15:05', 'firstRun': '08:56', 'break': '12:10', 'route': '응암 → 신내'},
      },
    });

void main() {
  final m = _month();
  final me = m.drivers.single;

  test('turnKey picks the sheet variant, old data falls back to turn id', () {
    expect(m.turnFor(m.dutyOn(me, '2026-10-01')!)!.depart, '18:30');
    expect(m.turnFor(m.dutyOn(me, '2026-10-04')!)!.brk, '12:10');
    expect(m.turnFor(m.dutyOn(me, '2026-10-03')!), isNull);
    expect(m.turns['5']!.segments, isEmpty);
  });

  test('night turn status follows the clock across midnight', () {
    DutyStatus at(int day, int h, int min) => dutyStatus(m, me, DateTime(2026, 10, day, h, min));

    final before = at(1, 17, 0);
    expect(before.phase, DutyPhase.before);
    expect(describeDutyStatus(before, DateTime(2026, 10, 1, 17)).$2, '오늘 출근 18:30 · 1시간 30분 후');

    final running = at(1, 19, 30);
    expect(running.phase, DutyPhase.onDuty);
    expect(describeDutyStatus(running, DateTime(2026, 10, 1, 19, 30)).$1, '운행 중 · 6256열차 응암→봉화산');

    // 다음날 새벽: "70~" 날이지만 전날 교번이 아직 진행 중.
    final night = at(2, 2, 0);
    expect(night.phase, DutyPhase.onDuty);
    expect(night.today!.code, '70~');
    expect(night.segment!.kind, 'standby');
    expect(night.nextDeparture, DateTime(2026, 10, 2, 5, 10));
    final (title, meta) = describeDutyStatus(night, DateTime(2026, 10, 2, 2, 0));
    expect(title, '대기 중');
    expect(meta, '다음 출발 05:10 (약 3시간 10분 후) · 퇴근 07:10');

    expect(at(2, 6, 0).segment!.train, '6271');
    expect(at(2, 8, 0).phase, DutyPhase.done);
    expect(at(3, 9, 0).phase, DutyPhase.none);
    expect(at(4, 9, 0).phase, DutyPhase.onDuty); // 옛 형식 주간 교번
  });

  test('근무 요약 counts', () {
    final s = dutySummary(m, me);
    expect((s.work, s.day, s.night, s.standby, s.off, s.rest), (2, 1, 1, 0, 1, 1));
  });

  test('demo fixture follows the shared contract', () {
    final raw = File('assets/data/duty_2026_06.json').readAsStringSync();
    final demo = DutyMonth.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    expect(demo.turnDetailIsDummy, isFalse);
    for (final d in demo.drivers) {
      for (final duty in d.days.values) {
        if (duty.turnKey != null) expect(demo.turns[duty.turnKey], isNotNull, reason: duty.turnKey);
        if (duty.continues != null) expect(demo.turns[duty.continues], isNotNull, reason: duty.continues);
      }
    }
    expect(demo.turns.values.where((t) => t.segments.isNotEmpty).length, greaterThan(10));
  });
}
