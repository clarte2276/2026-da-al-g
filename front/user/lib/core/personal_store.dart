import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'duty_data.dart';

Map<String, dynamic>? pendingDutySwap(
  List<Map<String, dynamic>> posts,
  String driverName,
  String date,
) {
  for (final post in posts) {
    if (post['type'] != 'direct' || post['status'] != 'open') continue;
    if (post['requester_name'] != driverName && post['target_name'] != driverName) {
      continue;
    }
    if ((post['dates'] as List?)?.contains(date) ?? false) return post;
  }
  return null;
}

/// 기기에만 저장하는 개인 기록: 날짜별 메모와 교번 변경(덮어쓸 근무 코드).
/// (기관사, 날짜) 단위. 근무 화면은 [DutyMonth.dutyOn]을 거치므로 교번 변경이 저절로 반영된다.
class PersonalStore extends ChangeNotifier {
  PersonalStore._();
  static final PersonalStore instance = PersonalStore._();

  static const _prefsKey = 'personal_v1';

  // 기관사 키 → 날짜 → 값
  Map<String, Map<String, String>> _memos = {};
  Map<String, Map<String, String>> _overrides = {};
  Map<String, Map<String, List<String>>> _overrideHistory = {};

  static String _driverKey(Driver d) => d.empNo ?? d.name;

  Future<void> init() async {
    final raw = (await SharedPreferences.getInstance()).getString(_prefsKey);
    if (raw == null) return;
    Map<String, Map<String, String>> read(Object? m) => (m as Map<String, dynamic>? ?? {})
        .map((k, v) => MapEntry(k, (v as Map<String, dynamic>).cast<String, String>()));
    final j = jsonDecode(raw) as Map<String, dynamic>;
    _memos = read(j['memo']);
    _overrides = read(j['override']);
    _overrideHistory = (j['overrideHistory'] as Map<String, dynamic>? ?? {})
        .map(
          (driver, dates) => MapEntry(
            driver,
            (dates as Map<String, dynamic>).map(
              (date, codes) =>
                  MapEntry(date, (codes as List).cast<String>().toList()),
            ),
          ),
        );
  }

  String? memo(Driver d, String date) => _memos[_driverKey(d)]?[date];

  /// 날짜 → 사용자가 바꿔 넣은 근무 코드.
  Map<String, String> overrides(Driver d) => _overrides[_driverKey(d)] ?? const {};

  Future<void> setMemo(Driver d, String date, String? text) => _set(_memos, d, date, text);

  /// null이면 원래 교번으로 되돌린다. 교번 변경 이력은 최근 20개까지만 남긴다.
  Future<void> setOverride(Driver d, String date, String? code) async {
    final key = _driverKey(d);
    final next = code?.trim() ?? '';
    final current = _overrides[key]?[date];
    if (next.isEmpty) {
      _overrides[key]?.remove(date);
      _overrideHistory[key]?.remove(date);
    } else {
      if (current == next) return;
      if (current != null) {
        final history = _overrideHistory
            .putIfAbsent(key, () => {})
            .putIfAbsent(date, () => []);
        history.add(current);
        if (history.length > 20) history.removeAt(0);
      }
      _overrides.putIfAbsent(key, () => {})[date] = next;
    }
    notifyListeners();
    await _save();
  }

  String? previousOverride(Driver d, String date) =>
      _overrideHistory[_driverKey(d)]?[date]?.lastOrNull;

  Future<void> undoOverride(Driver d, String date) async {
    final history = _overrideHistory[_driverKey(d)]?[date];
    if (history == null || history.isEmpty) return;
    _overrides.putIfAbsent(_driverKey(d), () => {})[date] = history
        .removeLast();
    if (history.isEmpty) _overrideHistory[_driverKey(d)]?.remove(date);
    notifyListeners();
    await _save();
  }

  Future<void> _set(Map<String, Map<String, String>> map, Driver d, String date, String? value) async {
    final byDate = map.putIfAbsent(_driverKey(d), () => {});
    final v = value?.trim() ?? '';
    if (v.isEmpty) {
      byDate.remove(date);
    } else {
      byDate[date] = v;
    }
    notifyListeners();
    await _save();
  }

  Future<void> _save() async {
    await (await SharedPreferences.getInstance()).setString(
      _prefsKey,
      jsonEncode({
        'memo': _memos,
        'override': _overrides,
        'overrideHistory': _overrideHistory,
      }),
    );
  }
}
