import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:user/core/duty_data.dart';
import 'package:user/core/personal_store.dart';

void main() {
  test(
    'keeps 20 override steps, can undo/reset, and reads legacy data',
    () async {
      SharedPreferences.setMockInitialValues({});
      final store = PersonalStore.instance;
      const driver = Driver(
        no: 1,
        name: '기록용',
        empNo: 'history-test',
        days: {},
      );
      const date = '2099-01-01';

      for (var code = 1; code <= 22; code++) {
        await store.setOverride(driver, date, '$code');
      }
      expect(store.previousOverride(driver, date), '21');
      final saved =
          jsonDecode(
                (await SharedPreferences.getInstance()).getString(
                  'personal_v1',
                )!,
              )
              as Map<String, dynamic>;
      expect(
        (saved['overrideHistory'] as Map)['history-test'][date],
        hasLength(20),
      );

      await store.undoOverride(driver, date);
      expect(store.overrides(driver)[date], '21');
      expect(store.previousOverride(driver, date), '20');
      await store.setOverride(driver, date, null);
      expect(store.overrides(driver).containsKey(date), isFalse);
      expect(store.previousOverride(driver, date), isNull);

      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(
        'personal_v1',
        jsonEncode({
          'memo': {
            'history-test': {date: 'old memo'},
          },
          'override': {
            'history-test': {date: '8'},
          },
        }),
      );
      await store.init();
      expect(store.memo(driver, date), 'old memo');
      expect(store.overrides(driver)[date], '8');
      expect(store.previousOverride(driver, date), isNull);
    },
  );
}
