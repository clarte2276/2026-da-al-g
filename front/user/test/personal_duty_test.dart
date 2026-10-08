import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:user/core/duty_data.dart';
import 'package:user/core/personal_store.dart';
import 'package:user/services/duty_alarm.dart';

// 2026-10-01(목) ~ 10-05(월). 10-03·04는 주말(휴).
DutyMonth _month() => DutyMonth.fromJson({
      'month': '2026-10',
      'dates': ['2026-10-01', '2026-10-02', '2026-10-03', '2026-10-04', '2026-10-05'],
      'drivers': [
        {
          'no': 1,
          'name': '가동훈',
          'empNo': '21714093',
          'days': {
            '2026-10-01': {'code': '5', 'type': 'day', 'turn': '5', 'dayType': '평', 'turnKey': '평평:5'},
            '2026-10-02': {'code': '70', 'type': 'night', 'turn': '70', 'dayType': '평', 'turnKey': '평휴:70'},
            '2026-10-03': {'code': '70~', 'type': 'off', 'dayType': '휴', 'continues': '평휴:70'},
            '2026-10-04': {'code': '대5', 'type': 'standby', 'dayType': '휴'},
            '2026-10-05': {'code': '휴19', 'type': 'rest', 'dayType': '평'},
          },
        },
      ],
      'turns': {
        '평평:5': {'id': '5', 'type': 'day', 'depart': '06:12', 'arrive': '14:00'},
        '휴휴:5': {'id': '5', 'type': 'day', 'depart': '07:00', 'arrive': '15:00'},
        '평휴:70': {'id': '70', 'type': 'night', 'depart': '18:31', 'arrive': '07:12', 'nextDay': true},
        '평평:61': {'id': '61', 'type': 'night', 'depart': '17:50', 'arrive': '06:40', 'nextDay': true},
      },
    });

void main() {
  final m = _month();
  final me = m.drivers.single;

  group('resolveDuty', () {
    test('no override passes the sheet through', () {
      final d = resolveDuty(m, me, '2026-10-01', {})!;
      expect(d.turnKey, '평평:5');
      expect(d.original, isNull);
    });

    test('dia on a 대기 day picks the 휴휴 sheet and remembers the original', () {
      final d = resolveDuty(m, me, '2026-10-04', {'2026-10-04': '5'})!;
      expect(d.type, DutyType.day);
      expect(d.turnKey, '휴휴:5');
      expect(d.original!.code, '대5');
      expect(m.turnFor(d)!.depart, '07:00');
    });

    test('night dia uses the D+D+1 combo (weekday fallback past the month)', () {
      final d = resolveDuty(m, me, '2026-10-05', {'2026-10-05': '61'})!;
      expect(d.turnKey, '평평:61');
      expect(d.type, DutyType.night);
    });

    test('swapping the night away drops the "70~" carry-over', () {
      final o = {'2026-10-02': '5'};
      expect(resolveDuty(m, me, '2026-10-02', o)!.turnKey, '평평:5');
      final next = resolveDuty(m, me, '2026-10-03', o)!;
      expect(next.code, '70~');
      expect(next.continues, isNull);
    });

    test('non-numeric codes map to types', () {
      expect(resolveDuty(m, me, '2026-10-01', {'2026-10-01': '비'})!.type, DutyType.off);
      expect(resolveDuty(m, me, '2026-10-01', {'2026-10-01': '휴'})!.type, DutyType.rest);
      final s = resolveDuty(m, me, '2026-10-01', {'2026-10-01': '대62'})!;
      expect((s.type, standbyLabel(s), m.turnFor(s)), (DutyType.standby, '야간대기', null));
    });

    test('dutyOn reads PersonalStore overrides; revert restores', () async {
      SharedPreferences.setMockInitialValues({});
      await PersonalStore.instance.setOverride(me, '2026-10-04', '5');
      expect(m.dutyOn(me, '2026-10-04')!.turnKey, '휴휴:5');
      await PersonalStore.instance.setOverride(me, '2026-10-04', null);
      expect(m.dutyOn(me, '2026-10-04')!.code, '대5');
    });
  });

  group('computeDutyAlarms', () {
    final now = DateTime(2026, 9, 30, 22);
    List<(DateTime, String)> run(Map<String, String> o) =>
        computeDutyAlarms([m], '가동훈', o, leadMinutes: 30, eveBefore: true, now: now)
            .map((a) => (a.at, a.title))
            .toList();

    test('lead + evening alarms, past ones dropped, standby excluded', () {
      expect(run({}), [
        (DateTime(2026, 10, 1, 5, 42), '출근 30분 전'),
        (DateTime(2026, 10, 1, 21), '내일 18:31 출근 · 70교번'),
        (DateTime(2026, 10, 2, 18, 1), '출근 30분 전'),
      ]);
    });

    test('override with a dia on the 대기 day adds its alarms', () {
      final a = run({'2026-10-04': '5'});
      expect(a, contains((DateTime(2026, 10, 3, 21), '내일 07:00 출근 · 5교번')));
      expect(a, contains((DateTime(2026, 10, 4, 6, 30), '출근 30분 전')));
      expect(a.length, 5);
    });

    test('off settings schedule nothing; dummy data schedules nothing', () {
      expect(computeDutyAlarms([m], '가동훈', {}, now: now), isEmpty);
      final dummy = DutyMonth.fromJson({
        'turnDetailIsDummy': true,
        'dates': ['2026-10-01'],
        'drivers': [
          {'name': '가동훈', 'days': {'2026-10-01': {'code': '5', 'type': 'day', 'turn': '5'}}},
        ],
        'turns': {'5': {'id': '5', 'type': 'day', 'depart': '06:12', 'arrive': '14:00'}},
      });
      expect(computeDutyAlarms([dummy], '가동훈', {}, leadMinutes: 10, now: now), isEmpty);
    });
  });
}

