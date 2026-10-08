import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'duty_data.dart';

/// 기기에만 저장하는 개인 기록: 날짜별 메모와 교번 변경(덮어쓸 근무 코드).
/// (기관사, 날짜) 단위. 근무 화면은 [DutyMonth.dutyOn]을 거치므로 교번 변경이 저절로 반영된다.
class PersonalStore extends ChangeNotifier {
  PersonalStore._();
  static final PersonalStore instance = PersonalStore._();

  static const _prefsKey = 'personal_v1';

  // 기관사 키 → 날짜 → 값
  Map<String, Map<String, String>> _memos = {};
  Map<String, Map<String, String>> _overrides = {};

  static String _driverKey(Driver d) => d.empNo ?? d.name;

  Future<void> init() async {
    final raw = (await SharedPreferences.getInstance()).getString(_prefsKey);
    if (raw == null) return;
    Map<String, Map<String, String>> read(Object? m) => (m as Map<String, dynamic>? ?? {})
        .map((k, v) => MapEntry(k, (v as Map<String, dynamic>).cast<String, String>()));
    final j = jsonDecode(raw) as Map<String, dynamic>;
    _memos = read(j['memo']);
    _overrides = read(j['override']);
  }

  String? memo(Driver d, String date) => _memos[_driverKey(d)]?[date];

  /// 날짜 → 사용자가 바꿔 넣은 근무 코드.
  Map<String, String> overrides(Driver d) => _overrides[_driverKey(d)] ?? const {};

  Future<void> setMemo(Driver d, String date, String? text) => _set(_memos, d, date, text);

  /// null이면 원래 교번으로 되돌린다.
  Future<void> setOverride(Driver d, String date, String? code) => _set(_overrides, d, date, code);

  Future<void> _set(Map<String, Map<String, String>> map, Driver d, String date, String? value) async {
    final byDate = map.putIfAbsent(_driverKey(d), () => {});
    final v = value?.trim() ?? '';
    if (v.isEmpty) {
      byDate.remove(date);
    } else {
      byDate[date] = v;
    }
    notifyListeners();
    await (await SharedPreferences.getInstance())
        .setString(_prefsKey, jsonEncode({'memo': _memos, 'override': _overrides}));
  }
}
