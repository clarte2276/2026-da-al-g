import 'package:flutter_test/flutter_test.dart';
import 'package:user/core/duty_data.dart';
import 'package:user/services/duty_alarm.dart';

const _allRules = <DutyAlarmRule, bool>{
  DutyAlarmRule.preparationBefore: true,
  DutyAlarmRule.firstRunAfter: true,
  DutyAlarmRule.nextTrainSignatureBefore: true,
  DutyAlarmRule.nextTrainDepartureBefore: true,
  DutyAlarmRule.depotDepartureBefore: true,
};

DutyMonth _month({
  required String date,
  required String code,
  required String type,
  required String depart,
  required String arrive,
  required List<Map<String, Object>> trainTimes,
}) {
  return DutyMonth.fromJson({
    'month': date.substring(0, 7),
    'dates': [date],
    'drivers': [
      {
        'name': '테스트 기사',
        'days': {
          date: {
            'code': code,
            'type': type,
            'turn': code,
            'turnKey': '평평:$code',
          },
        },
      },
    ],
    'turns': {
      '평평:$code': {
        'id': code,
        'type': type,
        'depart': depart,
        'arrive': arrive,
        'nextDay': type == 'night',
        'trainTimes': trainTimes,
      },
    },
  });
}

List<DutyAlarmItem> _alarms(DutyMonth month, DateTime now, {int days = 30}) =>
    computeDutyAlarms(
      [month],
      '테스트 기사',
      const {},
      rules: _allRules,
      now: now,
      days: days,
    );

void main() {
  test(
    'builds preparation, first-run, signature and departure alarm times',
    () {
      final month = _month(
        date: '2026-07-20',
        code: '5',
        type: 'day',
        depart: '06:26',
        arrive: '14:00',
        trainTimes: const [
          {'time': '12:25', 'depot': false},
        ],
      );

      expect(
        _alarms(month, DateTime(2026, 7, 20)).map((a) => (a.at, a.title)),
        [
          (DateTime(2026, 7, 20, 5, 26), '출근 준비하세요'),
          (DateTime(2026, 7, 20, 6, 46), '출장하세요'),
          (DateTime(2026, 7, 20, 11, 45), '서명하세요'),
          (DateTime(2026, 7, 20, 12, 15), '출장하세요'),
        ],
      );
    },
  );

  test(
    'a depot time gets one combined alarm; regular times get signature and departure',
    () {
      final month = _month(
        date: '2026-07-20',
        code: '7',
        type: 'day',
        depart: '06:36',
        arrive: '17:00',
        trainTimes: const [
          {'time': '08:26', 'depot': false},
          {'time': '12:10', 'depot': true},
        ],
      );

      expect(
        _alarms(month, DateTime(2026, 7, 20)).map((a) => (a.at, a.title)),
        [
          (DateTime(2026, 7, 20, 5, 36), '출근 준비하세요'),
          (DateTime(2026, 7, 20, 6, 56), '출장하세요'),
          (DateTime(2026, 7, 20, 7, 46), '서명하세요'),
          (DateTime(2026, 7, 20, 8, 16), '출장하세요'),
          (DateTime(2026, 7, 20, 11), '서명 및 출장하세요'),
        ],
      );
    },
  );

  test('honors rule toggles and custom minutes', () {
    final month = _month(
      date: '2026-07-20',
      code: '5',
      type: 'day',
      depart: '06:26',
      arrive: '14:00',
      trainTimes: const [
        {'time': '12:25', 'depot': false},
      ],
    );

    final alarms = computeDutyAlarms(
      [month],
      '테스트 기사',
      const {},
      rules: const {DutyAlarmRule.preparationBefore: true},
      minutes: const {DutyAlarmRule.preparationBefore: 45},
      now: DateTime(2026, 7, 20),
    );
    expect(alarms.map((a) => (a.at, a.title)), [
      (DateTime(2026, 7, 20, 5, 41), '출근 준비하세요'),
    ]);
  });

  test('rolls a night turn train time past midnight', () {
    final month = _month(
      date: '2026-07-20',
      code: '64',
      type: 'night',
      depart: '17:57',
      arrive: '06:40',
      trainTimes: const [
        {'time': '06:43', 'depot': true},
      ],
    );

    expect(
      _alarms(month, DateTime(2026, 7, 20)).map((a) => (a.at, a.title)),
      containsAll([(DateTime(2026, 7, 21, 5, 33), '서명 및 출장하세요')]),
    );
  });

  test('includes remaining alarms from a night turn started yesterday', () {
    final month = DutyMonth.fromJson({
      'month': '2026-07',
      'dates': ['2026-07-20', '2026-07-21'],
      'drivers': [
        {
          'name': '테스트 기사',
          'days': {
            '2026-07-20': {
              'code': '75',
              'type': 'night',
              'turn': '75',
              'turnKey': '평평:75',
            },
            '2026-07-21': {'code': '75~', 'type': 'off', 'continues': '평평:75'},
          },
        },
      ],
      'turns': {
        '평평:75': {
          'id': '75',
          'type': 'night',
          'depart': '18:59',
          'arrive': '06:00',
          'nextDay': true,
          'trainTimes': [
            {'time': '23:01', 'depot': false},
            {'time': '05:37', 'depot': false},
          ],
        },
      },
    });

    expect(
      _alarms(
        month,
        DateTime(2026, 7, 21, 1),
        days: 1,
      ).map((a) => (a.at, a.title)),
      [
        (DateTime(2026, 7, 21, 4, 57), '서명하세요'),
        (DateTime(2026, 7, 21, 5, 27), '출장하세요'),
      ],
    );
  });

  test('skips standby days even when they have a turn assigned', () {
    final month = _month(
      date: '2026-07-20',
      code: '대5',
      type: 'standby',
      depart: '06:26',
      arrive: '14:00',
      trainTimes: const [
        {'time': '12:25', 'depot': false},
      ],
    );

    expect(_alarms(month, DateTime(2026, 7, 20)), isEmpty);
  });
}
