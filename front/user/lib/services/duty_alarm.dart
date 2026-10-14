import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:timezone/data/latest.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

import '../core/duty_data.dart';
import '../core/personal_store.dart';
import 'auth_session.dart';

enum DutyAlarmRule {
  preparationBefore,
  firstRunAfter,
  nextTrainSignatureBefore,
  nextTrainDepartureBefore,
  depotDepartureBefore,
}

const dutyAlarmDefaultMinutes = <DutyAlarmRule, int>{
  DutyAlarmRule.preparationBefore: 60,
  DutyAlarmRule.firstRunAfter: 20,
  DutyAlarmRule.nextTrainSignatureBefore: 40,
  DutyAlarmRule.nextTrainDepartureBefore: 10,
  DutyAlarmRule.depotDepartureBefore: 70,
};

const dutyAlarmDefaultEnabled = <DutyAlarmRule, bool>{
  DutyAlarmRule.preparationBefore: false,
  DutyAlarmRule.firstRunAfter: true,
  DutyAlarmRule.nextTrainSignatureBefore: true,
  DutyAlarmRule.nextTrainDepartureBefore: true,
  DutyAlarmRule.depotDepartureBefore: true,
};

typedef DutyAlarmItem = ({DateTime at, String title, String body});

int? _minutes(String value) {
  final match = RegExp(r'^(\d{1,2}):(\d{2})$').firstMatch(value.trim());
  if (match == null) return null;
  final hours = int.parse(match[1]!);
  final minutes = int.parse(match[2]!);
  if (hours > 23 || minutes > 59) return null;
  return hours * 60 + minutes;
}

String _hm(DateTime time) =>
    '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';

List<DutyAlarmItem> computeDutyAlarms(
  List<DutyMonth> months,
  String? driverName,
  Map<String, String> overrides, {
  Map<DutyAlarmRule, bool>? rules,
  Map<DutyAlarmRule, int>? minutes,
  bool eveBefore = false,
  required DateTime now,
  int days = 30,
  // Kept for callers from the old one-rule settings until their next release.
  int? leadMinutes,
}) {
  final legacyLead = leadMinutes != null;
  final enabled =
      rules ??
      (legacyLead
          ? const {DutyAlarmRule.preparationBefore: true}
          : const <DutyAlarmRule, bool>{});
  final timing = minutes ?? dutyAlarmDefaultMinutes;
  final out = <DutyAlarmItem>[];

  for (var offset = -1; offset < days; offset++) {
    final date = DateTime(now.year, now.month, now.day + offset);
    final key = dutyDateKey(date);
    final month = months
        .where((m) => m.dates.contains(key) && !m.turnDetailIsDummy)
        .firstOrNull;
    final driver = month?.driverNamed(driverName);
    if (month == null || driver == null) continue;
    final duty = resolveDuty(month, driver, key, overrides);
    if (duty == null || duty.type == DutyType.standby) continue;
    final turn = month.turnFor(duty);
    final start = turn?.timesOn(date)?.$1;
    if (turn == null || start == null) continue;

    void add(DateTime at, String title, String body) {
      if (at.isAfter(now)) out.add((at: at, title: title, body: body));
    }

    if (enabled[DutyAlarmRule.preparationBefore] == true) {
      final lead = leadMinutes ?? timing[DutyAlarmRule.preparationBefore]!;
      add(
        start.subtract(Duration(minutes: lead)),
        legacyLead ? '출근 $lead분 전' : '출근 준비하세요',
        '${_hm(start)} 출근 · ${turn.id}교번',
      );
    }
    if (!legacyLead && enabled[DutyAlarmRule.firstRunAfter] == true) {
      add(
        start.add(Duration(minutes: timing[DutyAlarmRule.firstRunAfter]!)),
        '출장하세요',
        '${_hm(start)} 출근 · ${turn.id}교번',
      );
    }

    var previousTrain = start;
    for (final train in turn.trainTimes) {
      final trainMinutes = _minutes(train.time);
      if (trainMinutes == null) continue;
      var trainAt = DateTime(
        date.year,
        date.month,
        date.day,
      ).add(Duration(minutes: trainMinutes));
      while (!trainAt.isAfter(previousTrain)) {
        trainAt = trainAt.add(const Duration(days: 1));
      }
      previousTrain = trainAt;
      if (legacyLead) continue;
      if (train.depot) {
        if (enabled[DutyAlarmRule.depotDepartureBefore] == true) {
          add(
            trainAt.subtract(
              Duration(minutes: timing[DutyAlarmRule.depotDepartureBefore]!),
            ),
            '서명 및 출장하세요',
            '${train.time} 출고 열차 · ${turn.id}교번',
          );
        }
      } else {
        if (enabled[DutyAlarmRule.nextTrainSignatureBefore] == true) {
          add(
            trainAt.subtract(
              Duration(
                minutes: timing[DutyAlarmRule.nextTrainSignatureBefore]!,
              ),
            ),
            '서명하세요',
            '${train.time} 열차 · ${turn.id}교번',
          );
        }
        if (enabled[DutyAlarmRule.nextTrainDepartureBefore] == true) {
          add(
            trainAt.subtract(
              Duration(
                minutes: timing[DutyAlarmRule.nextTrainDepartureBefore]!,
              ),
            ),
            '출장하세요',
            '${train.time} 열차 · ${turn.id}교번',
          );
        }
      }
    }

    final eve = DateTime(date.year, date.month, date.day - 1, 21);
    if (eveBefore && eve.isAfter(now) && eve.isBefore(start)) {
      add(
        eve,
        '내일 ${_hm(start)} 출근 · ${turn.id}교번',
        '${duty.type.label} ${duty.code}',
      );
    }
  }
  out.sort((a, b) => a.at.compareTo(b.at));
  return out;
}

class DutyAlarm extends ChangeNotifier {
  DutyAlarm._();
  static final DutyAlarm instance = DutyAlarm._();

  static const _leadKey = 'alarm_lead_minutes';
  static const _eveKey = 'alarm_eve_before';
  static const _channelId = 'duty_alarm_v2';

  final rules = {...dutyAlarmDefaultEnabled};
  final minutes = {...dutyAlarmDefaultMinutes};
  bool eveBefore = false;
  List<DutyAlarmItem> upcoming = [];
  bool? fullScreenAllowed;

  bool get supported =>
      !kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.android ||
          defaultTargetPlatform == TargetPlatform.iOS);
  bool get anyEnabled => eveBefore || rules.values.any((value) => value);

  final _plugin = FlutterLocalNotificationsPlugin();
  tz.Location? _seoul;
  Future<void> _queue = Future.value();

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    final oldLead = prefs.getInt(_leadKey);
    for (final rule in DutyAlarmRule.values) {
      final suffix = rule.name;
      minutes[rule] =
          prefs.getInt('duty_alarm_${suffix}_minutes') ??
          (rule == DutyAlarmRule.preparationBefore
              ? oldLead ?? dutyAlarmDefaultMinutes[rule]!
              : dutyAlarmDefaultMinutes[rule]!);
      rules[rule] =
          prefs.getBool('duty_alarm_${suffix}_enabled') ??
          (rule == DutyAlarmRule.preparationBefore &&
                  prefs.containsKey(_leadKey)
              ? oldLead != null
              : dutyAlarmDefaultEnabled[rule]!);
    }
    eveBefore = prefs.getBool(_eveKey) ?? false;
    if (prefs.containsKey(_leadKey)) {
      await prefs.setInt(
        'duty_alarm_preparationBefore_minutes',
        minutes[DutyAlarmRule.preparationBefore]!,
      );
      await prefs.setBool(
        'duty_alarm_preparationBefore_enabled',
        oldLead != null,
      );
      await prefs.remove(_leadKey);
    }
    PersonalStore.instance.addListener(reschedule);
    unawaited(reschedule());
  }

  Future<void> setRuleEnabled(DutyAlarmRule rule, bool value) async {
    rules[rule] = value;
    notifyListeners();
    await (await SharedPreferences.getInstance()).setBool(
      'duty_alarm_${rule.name}_enabled',
      value,
    );
    if (value) await _requestPermission();
    await reschedule();
  }

  Future<void> setMinutes(DutyAlarmRule rule, int value) async {
    final max = rule == DutyAlarmRule.firstRunAfter ? 120 : 180;
    if (value < 0 || value > max) throw ArgumentError.value(value, 'minutes');
    minutes[rule] = value;
    notifyListeners();
    await (await SharedPreferences.getInstance()).setInt(
      'duty_alarm_${rule.name}_minutes',
      value,
    );
    await reschedule();
  }

  Future<void> setEveBefore(bool value) async {
    eveBefore = value;
    notifyListeners();
    await (await SharedPreferences.getInstance()).setBool(_eveKey, value);
    if (value) await _requestPermission();
    await reschedule();
  }

  Future<void> _requestPermission() async {
    if (!supported) return;
    await _ensureInit();
    final android = _plugin
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >();
    await android?.requestNotificationsPermission();
    if (android != null &&
        !(await android.canScheduleExactNotifications() ?? false)) {
      await android.requestExactAlarmsPermission();
    }
    await _plugin
        .resolvePlatformSpecificImplementation<
          IOSFlutterLocalNotificationsPlugin
        >()
        ?.requestPermissions(alert: true, badge: true, sound: true);
  }

  Future<bool> exactAlarmsAllowed() async {
    final android = _plugin
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >();
    return android == null ||
        (await android.canScheduleExactNotifications() ?? false);
  }

  Future<bool> openExactAlarmSettings() async {
    final android = _plugin
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >();
    if (android == null) return true;
    if (await android.canScheduleExactNotifications() ?? false) return true;
    await android.requestExactAlarmsPermission();
    return await android.canScheduleExactNotifications() ?? false;
  }

  Future<bool?> openFullScreenSettings() async {
    final android = _plugin
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >();
    if (android == null) return true;
    fullScreenAllowed = await android.requestFullScreenIntentPermission();
    notifyListeners();
    return fullScreenAllowed;
  }

  Future<void> sendTestNotification() async {
    await _requestPermission();
    await _ensureInit();
    await _plugin.show(
      id: 2147483000,
      title: '근무 알림 테스트',
      body: '근무 알림이 정상적으로 도착합니다.',
      notificationDetails: _details,
    );
  }

  Future<void> reschedule() =>
      _queue = _queue.then((_) => _reschedule()).catchError((Object e) {
        debugPrint('duty alarm: $e');
      });

  Future<int> recalculate() async {
    await reschedule();
    return upcoming.length;
  }

  Future<void> _ensureInit() async {
    if (_seoul != null) return;
    tzdata.initializeTimeZones();
    await _plugin.initialize(
      settings: const InitializationSettings(
        android: AndroidInitializationSettings('@mipmap/ic_launcher'),
        iOS: DarwinInitializationSettings(
          requestAlertPermission: false,
          requestBadgePermission: false,
          requestSoundPermission: false,
        ),
      ),
    );
    _seoul = tz.getLocation('Asia/Seoul');
  }

  static const _details = NotificationDetails(
    android: AndroidNotificationDetails(
      _channelId,
      '근무 알림',
      channelDescription: '근무 시간에 맞춰 알립니다.',
      importance: Importance.max,
      priority: Priority.max,
      category: AndroidNotificationCategory.alarm,
      fullScreenIntent: true,
    ),
    iOS: DarwinNotificationDetails(),
  );

  Future<void> _reschedule() async {
    if (!supported) return;
    await _ensureInit();
    await _plugin.cancelAll();
    upcoming = [];
    final name = AuthSession.current?.user.name;
    if (!anyEnabled || name == null) {
      notifyListeners();
      return;
    }

    final now = DateTime.now();
    final first = DateTime(now.year, now.month, now.day - 1);
    final last = DateTime(now.year, now.month, now.day + 29);
    final monthsToLoad = <String>{};
    for (
      var day = first;
      !day.isAfter(last);
      day = day.add(const Duration(days: 1))
    ) {
      monthsToLoad.add('${day.year}-${day.month.toString().padLeft(2, '0')}');
    }
    final months = <DutyMonth>[];
    for (final month in monthsToLoad) {
      try {
        months.add(await DutyRepository.instance.load(month));
      } catch (_) {
        // A missing month can be filled the next time the schedule is refreshed.
      }
    }
    final driver = months
        .map((month) => month.driverNamed(name))
        .nonNulls
        .firstOrNull;
    if (driver == null) {
      notifyListeners();
      return;
    }
    upcoming = computeDutyAlarms(
      months,
      name,
      PersonalStore.instance.overrides(driver),
      rules: rules,
      minutes: minutes,
      eveBefore: eveBefore,
      now: now,
    );

    final android = _plugin
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >();
    if (android != null &&
        !(await android.canScheduleExactNotifications() ?? false)) {
      notifyListeners();
      return;
    }
    final scheduled = android == null ? upcoming.take(60).toList() : upcoming;
    for (var i = 0; i < scheduled.length; i++) {
      final alarm = scheduled[i];
      await _plugin.zonedSchedule(
        id: i,
        scheduledDate: tz.TZDateTime(
          _seoul!,
          alarm.at.year,
          alarm.at.month,
          alarm.at.day,
          alarm.at.hour,
          alarm.at.minute,
        ),
        notificationDetails: _details,
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
        title: alarm.title,
        body: alarm.body,
      );
    }
    notifyListeners();
  }
}
