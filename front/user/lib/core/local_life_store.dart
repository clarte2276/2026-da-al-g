import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

/// 기기에만 저장하는 힐링카드·플래너 데이터.
String monthKey(DateTime d) => '${d.year}-${d.month.toString().padLeft(2, '0')}';

class HealingCard {
  HealingCard(this.limit, this.entries);
  int limit;

  /// 월(YYYY-MM)별 사용 내역. 달이 바뀌면 새 달의 빈 목록에서 시작한다(월별 초기화).
  final Map<String, List<Map<String, dynamic>>> entries;

  static const _key = 'life.healing_card';

  List<Map<String, dynamic>> month(DateTime d) => entries[monthKey(d)] ?? [];
  int spent(DateTime d) => month(d).fold(0, (sum, e) => sum + (e['amount'] as int));
  int balance(DateTime d) => limit - spent(d);

  void add(DateTime d, int amount, String memo) =>
      entries.putIfAbsent(monthKey(d), () => []).add({'amount': amount, 'memo': memo, 'at': d.toIso8601String()});

  void remove(DateTime d, int index) => entries[monthKey(d)]?.removeAt(index);

  static Future<HealingCard> load() async {
    final raw = (await SharedPreferences.getInstance()).getString(_key);
    if (raw == null) return HealingCard(0, {});
    final json = jsonDecode(raw) as Map<String, dynamic>;
    return HealingCard(json['limit'] as int, {
      for (final e in (json['entries'] as Map<String, dynamic>).entries)
        e.key: (e.value as List).cast<Map<String, dynamic>>(),
    });
  }

  Future<void> save() async =>
      (await SharedPreferences.getInstance()).setString(_key, jsonEncode({'limit': limit, 'entries': entries}));
}

class Planner {
  Planner(this.todos, this.events, this.memo);

  /// {text, done}
  final List<Map<String, dynamic>> todos;

  /// {date: YYYY-MM-DD, title} — 날짜순 정렬 유지.
  final List<Map<String, dynamic>> events;
  String memo;

  static const _key = 'life.planner';

  void addEvent(String date, String title) {
    events.add({'date': date, 'title': title});
    events.sort((a, b) => (a['date'] as String).compareTo(b['date'] as String));
  }

  List<Map<String, dynamic>> upcoming(DateTime today) {
    final key = '${monthKey(today)}-${today.day.toString().padLeft(2, '0')}';
    return events.where((e) => (e['date'] as String).compareTo(key) >= 0).toList();
  }

  static Future<Planner> load() async {
    final raw = (await SharedPreferences.getInstance()).getString(_key);
    if (raw == null) return Planner([], [], '');
    final json = jsonDecode(raw) as Map<String, dynamic>;
    return Planner(
      (json['todos'] as List).cast<Map<String, dynamic>>(),
      (json['events'] as List).cast<Map<String, dynamic>>(),
      json['memo'] as String? ?? '',
    );
  }

  Future<void> save() async =>
      (await SharedPreferences.getInstance()).setString(_key, jsonEncode({'todos': todos, 'events': events, 'memo': memo}));
}
