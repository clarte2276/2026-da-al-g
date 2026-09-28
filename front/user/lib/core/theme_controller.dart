import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// 앱 전역 테마 모드(시스템/라이트/다크). 선택은 저장되고, 시스템 모드면 기기 설정 변화를 따른다.
class ThemeController extends ChangeNotifier with WidgetsBindingObserver {
  ThemeController._();
  static final ThemeController instance = ThemeController._();

  static const _key = 'theme_mode';

  ThemeMode _mode = ThemeMode.system;
  ThemeMode get mode => _mode;

  bool get isDark => switch (_mode) {
    ThemeMode.dark => true,
    ThemeMode.light => false,
    ThemeMode.system =>
      WidgetsBinding.instance.platformDispatcher.platformBrightness ==
          Brightness.dark,
  };

  Future<void> init() async {
    WidgetsBinding.instance.addObserver(this);
    final prefs = await SharedPreferences.getInstance();
    _mode = ThemeMode.values.asNameMap()[prefs.getString(_key)] ?? ThemeMode.system;
  }

  Future<void> setMode(ThemeMode mode) async {
    if (_mode == mode) return;
    _mode = mode;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_key, mode.name);
  }

  @override
  void didChangePlatformBrightness() {
    if (_mode == ThemeMode.system) notifyListeners();
  }
}
