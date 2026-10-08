import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:timezone/data/latest.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;
import '../core/duty_data.dart';
import '../core/personal_store.dart';
import 'auth_session.dart';

typedef DutyAlarmItem = ({DateTime at, String title, String body});

String _hm(DateTime t) => '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';

/// [now]부터 [days]일 동안 울릴 알람(순수 함수). 시각은 서울 기준 벽시계 시각.
/// - [leadMinutes]: 출근 N분 전 (null이면 끔)
/// - [eveBefore]: 전날 21:00 "내일 06:12 출근 · 5교번"
/// 행로표가 없는 날(대기 등)은 건너뛴다. 교번 변경으로 dia를 넣으면 그 dia로 울린다.
List<DutyAlarmItem> computeDutyAlarms(
  List<DutyMonth> months,
  String? driverName,
  Map<String, String> overrides, {
  int? leadMinutes,
  bool eveBefore = false,
  required DateTime now,
  int days = 14,
}) {
  final out = <DutyAlarmItem>[];
  for (var i = 0; i < days; i++) {
    final date = DateTime(now.year, now.month, now.day + i);
    final key = dutyDateKey(date);
    final m = months.where((m) => m.dates.contains(key) && !m.turnDetailIsDummy).firstOrNull;
    final driver = m?.driverNamed(driverName);
    if (m == null || driver == null) continue;
    final duty = resolveDuty(m, driver, key, overrides);
    if (duty == null || duty.type == DutyType.standby) continue;
    final turn = m.turnFor(duty);
    final start = turn?.timesOn(date)?.$1;
    if (turn == null || start == null) continue;
    if (leadMinutes != null) {
      final at = start.subtract(Duration(minutes: leadMinutes));
      if (at.isAfter(now)) out.add((at: at, title: '출근 $leadMinutes분 전', body: '${_hm(start)} 출근 · ${turn.id}교번'));
    }
    final eve = DateTime(date.year, date.month, date.day - 1, 21);
    if (eveBefore && eve.isAfter(now) && eve.isBefore(start)) {
      out.add((at: eve, title: '내일 ${_hm(start)} 출근 · ${turn.id}교번', body: '${duty.type.label} ${duty.code}'));
    }
  }
  out.sort((a, b) => a.at.compareTo(b.at));
  return out;
}

/// 근무 알람 설정과 예약. Android/iOS에서만 동작하고 그 밖에서는 아무 일도 하지 않는다.
class DutyAlarm extends ChangeNotifier {
  DutyAlarm._();
  static final DutyAlarm instance = DutyAlarm._();

  static const leadChoices = [10, 20, 30, 60, 70];
  static const _leadKey = 'alarm_lead_minutes';
  static const _eveKey = 'alarm_eve_before';

  int? leadMinutes; // null = 끔
  bool eveBefore = false;

  bool get supported =>
      !kIsWeb && (defaultTargetPlatform == TargetPlatform.android || defaultTargetPlatform == TargetPlatform.iOS);

  final _plugin = FlutterLocalNotificationsPlugin();
  tz.Location? _seoul;
  Future<void> _queue = Future.value();

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    leadMinutes = prefs.getInt(_leadKey);
    eveBefore = prefs.getBool(_eveKey) ?? false;
    // 교번 변경이 바뀌면 다시 예약한다.
    PersonalStore.instance.addListener(reschedule);
    reschedule();
  }

  Future<void> setLeadMinutes(int? m) async {
    leadMinutes = m;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    m == null ? await prefs.remove(_leadKey) : await prefs.setInt(_leadKey, m);
    if (m != null) await _requestPermission();
    reschedule();
  }

  Future<void> setEveBefore(bool on) async {
    eveBefore = on;
    notifyListeners();
    await (await SharedPreferences.getInstance()).setBool(_eveKey, on);
    if (on) await _requestPermission();
    reschedule();
  }

  /// 앞으로 14일 알람을 새로 잡는다. 겹쳐 불려도 차례로 돈다.
  Future<void> reschedule() => _queue = _queue.then((_) => _reschedule()).catchError((Object e) {
        debugPrint('duty alarm: $e');
      });

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

  Future<void> _requestPermission() async {
    if (!supported) return;
    await _ensureInit();
    final android = _plugin.resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();
    await android?.requestNotificationsPermission();
    if (android != null && !(await android.canScheduleExactNotifications() ?? false)) {
      await android.requestExactAlarmsPermission(); // 거부해도 부정확 예약으로 동작
    }
    await _plugin
        .resolvePlatformSpecificImplementation<IOSFlutterLocalNotificationsPlugin>()
        ?.requestPermissions(alert: true, badge: true, sound: true);
  }

  Future<void> _reschedule() async {
    if (!supported) return;
    await _ensureInit();
    await _plugin.cancelAll();
    final name = AuthSession.current?.user.name;
    if ((leadMinutes == null && !eveBefore) || name == null) return;

    final now = DateTime.now();
    final months = <DutyMonth>[];
    for (final d in [now, DateTime(now.year, now.month + 1)]) {
      final month = '${d.year}-${d.month.toString().padLeft(2, '0')}';
      try {
        months.add(await DutyRepository.instance.load(month));
      } catch (_) {
        // 다음 달 근무표가 아직 없을 수 있다.
      }
    }
    final me = months.map((m) => m.driverNamed(name)).nonNulls.firstOrNull;
    if (me == null) return;
    final items = computeDutyAlarms(
      months,
      name,
      PersonalStore.instance.overrides(me),
      leadMinutes: leadMinutes,
      eveBefore: eveBefore,
      now: now,
    );

    final android = _plugin.resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();
    final exact = android == null || (await android.canScheduleExactNotifications() ?? false);
    const details = NotificationDetails(
      android: AndroidNotificationDetails(
        'duty_alarm',
        '근무 알람',
        channelDescription: '출근 전·전날 저녁 근무 알림',
        importance: Importance.high,
        priority: Priority.high,
      ),
      iOS: DarwinNotificationDetails(),
    );
    for (var i = 0; i < items.length; i++) {
      final a = items[i];
      await _plugin.zonedSchedule(
        id: i,
        scheduledDate: tz.TZDateTime(_seoul!, a.at.year, a.at.month, a.at.day, a.at.hour, a.at.minute),
        notificationDetails: details,
        androidScheduleMode: exact ? AndroidScheduleMode.exactAllowWhileIdle : AndroidScheduleMode.inexactAllowWhileIdle,
        title: a.title,
        body: a.body,
      );
    }
  }
}
