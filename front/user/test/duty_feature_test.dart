import 'package:flutter_test/flutter_test.dart';
import 'package:user/core/duty_data.dart';
import 'package:user/core/personal_store.dart';

void main() {
  test(
    'parses projected duties, swap originals, train times, and dia image',
    () {
      final month = DutyMonth.fromJson({
        'month': '2026-10',
        'line': '6호선',
        'office': '신내',
        'dates': ['2026-10-01'],
        'projected': true,
        'projectedFrom': '2026-06',
        'turnDetailIsDummy': false,
        'drivers': [
          {
            'no': 1,
            'name': '홍길동',
            'days': {
              '2026-10-01': {
                'code': '62',
                'type': 'night',
                'turn': '62',
                'turnKey': '평휴:62',
                'swapPostId': 'swap-1',
                'original': {'code': '61', 'type': 'night', 'turn': '61'},
              },
            },
          },
        ],
        'turns': {
          '평휴:62': {
            'id': '62',
            'type': 'night',
            'depart': '18:00',
            'arrive': '03:00',
            'firstRun': '18:20',
            'break': '00:00',
            'route': '응암 → 봉화산',
            'trainTimes': [
              {'time': '18:20', 'depot': true},
              {'time': '19:05', 'depot': false},
            ],
            'diaImage': '/api/duty/dia-images/hol-62.png',
          },
        },
      });

      final duty = month.drivers.single.days['2026-10-01']!;
      final turn = month.turnFor(duty)!;
      expect(month.projected, isTrue);
      expect(month.projectedFrom, '2026-06');
      expect(duty.original?.code, '61');
      expect(duty.swapPostId, 'swap-1');
      expect(turn.trainTimes, [
        (time: '18:20', depot: true),
        (time: '19:05', depot: false),
      ]);
      expect(turn.diaImage, '/api/duty/dia-images/hol-62.png');

      final local = resolveDuty(month, month.drivers.single, '2026-10-01', {
        '2026-10-01': '63',
      })!;
      expect(local.code, '63');
      expect(local.original?.code, '61');
      expect(local.swapPostId, 'swap-1');
    },
  );

  test('finds only an open direct swap involving this driver and date', () {
    final posts = [
      {
        'id': 'other-day',
        'type': 'direct',
        'status': 'open',
        'requester_name': '홍길동',
        'target_name': '김철수',
        'dates': ['2026-10-02'],
      },
      {
        'id': 'closed',
        'type': 'direct',
        'status': 'accepted',
        'requester_name': '홍길동',
        'target_name': '김철수',
        'dates': ['2026-10-01'],
      },
      {
        'id': 'pending',
        'type': 'direct',
        'status': 'open',
        'requester_name': '홍길동',
        'target_name': '김철수',
        'dates': ['2026-10-01'],
      },
    ];

    expect(pendingDutySwap(posts, '홍길동', '2026-10-01')?['id'], 'pending');
    expect(pendingDutySwap(posts, '이영희', '2026-10-01'), isNull);
  });
}
