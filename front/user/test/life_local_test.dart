import 'dart:math';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:user/core/games_logic.dart';
import 'package:user/core/local_life_store.dart';
import 'package:user/screens/menu_screen.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('힐링카드: 달마다 따로 집계하고 저장 후 다시 읽힌다', () async {
    final card = await HealingCard.load();
    card.limit = 100000;
    card.add(DateTime(2026, 9, 30), 30000, '마사지');
    card.add(DateTime(2026, 10, 1), 12000, '헬스');
    card.add(DateTime(2026, 10, 5), 8000, '요가');
    await card.save();

    final again = await HealingCard.load();
    expect(again.balance(DateTime(2026, 10, 20)), 80000);
    expect(again.balance(DateTime(2026, 9, 1)), 70000);
    expect(again.balance(DateTime(2026, 11, 1)), 100000); // 새 달은 한도 전액
    again.remove(DateTime(2026, 10, 9), 0);
    expect(again.spent(DateTime(2026, 10, 9)), 8000);
  });

  test('플래너: 일정은 날짜순, 지난 일정은 다가오는 목록에서 빠진다', () async {
    final p = await Planner.load();
    p.addEvent('2026-10-20', '교육');
    p.addEvent('2026-10-01', '지난 일');
    p.addEvent('2026-10-05', '오늘 일');
    p.todos.add({'text': '면허 갱신', 'done': false});
    p.memo = '메모';
    await p.save();

    final again = await Planner.load();
    expect(again.events.map((e) => e['date']), ['2026-10-01', '2026-10-05', '2026-10-20']);
    expect(again.upcoming(DateTime(2026, 10, 5)).map((e) => e['title']), ['오늘 일', '교육']);
    expect(again.todos.single['text'], '면허 갱신');
    expect(again.memo, '메모');
  });

  test('게임 문제: 암산 정답이 맞고 색깔 문제는 글자와 색이 다르다', () {
    final r = Random(1);
    for (var i = 0; i < 200; i++) {
      final q = MathQuestion.random(r);
      final m = RegExp(r'^(\d+) ([+\-×]) (\d+)$').firstMatch(q.text)!;
      final a = int.parse(m[1]!), b = int.parse(m[3]!);
      expect(q.answer, switch (m[2]) { '+' => a + b, '-' => a - b, _ => a * b });
      expect(q.answer, greaterThanOrEqualTo(0));
      final c = ColorQuestion.random(r, 4);
      expect(c.word, isNot(c.ink));
    }
    expect(lowerIsBetter('reaction'), isTrue);
    expect(lowerIsBetter('math'), isFalse);
  });

  test('ISO 주차', () {
    expect(isoWeek(DateTime(2026, 10, 5)), '2026-W41');
    expect(isoWeek(DateTime(2027, 1, 1)), '2026-W53');
    expect(isoWeek(DateTime(2026, 1, 1)), '2026-W01');
  });
}
