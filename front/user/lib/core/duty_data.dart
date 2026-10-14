import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/ai_api_client.dart';
import 'personal_store.dart';

/// 근무 유형. 엑셀 코드(비/휴/대/지정/숫자)를 파서가 분류한 결과와 1:1.
enum DutyType { day, night, off, rest, standby, designated, unknown }

DutyType _dutyTypeFrom(String? s) {
  switch (s) {
    case 'day':
      return DutyType.day;
    case 'night':
      return DutyType.night;
    case 'off':
      return DutyType.off;
    case 'rest':
      return DutyType.rest;
    case 'standby':
      return DutyType.standby;
    case 'designated':
      return DutyType.designated;
    default:
      return DutyType.unknown;
  }
}

extension DutyTypeMeta on DutyType {
  String get label {
    switch (this) {
      case DutyType.day:
        return '주간';
      case DutyType.night:
        return '야간';
      case DutyType.off:
        return '비번';
      case DutyType.rest:
        return '휴무';
      case DutyType.standby:
        return '대기';
      case DutyType.designated:
        return '지정';
      case DutyType.unknown:
        return '-';
    }
  }

  /// 근무(승무) 여부 — 교번 상세가 있는 유형.
  bool get isWork =>
      this == DutyType.day || this == DutyType.night || this == DutyType.standby;
}

class DayDuty {
  const DayDuty({
    required this.code,
    required this.type,
    this.turn,
    this.dayType,
    this.turnKey,
    this.continues,
    this.original,
    this.swapPostId,
  });
  final String code;
  final DutyType type;
  final String? turn;

  /// 그날의 평/휴 구분 ("평" | "휴").
  final String? dayType;

  /// `turns` 맵의 키 ("평평:70"). 옛 데이터에는 없어 [turn]으로 대신 찾는다.
  final String? turnKey;

  /// "70~" 같은 야간 다음날 아침: 전날부터 이어지는 교번의 turnKey.
  final String? continues;

  /// 교번 변경으로 덮어쓴 경우 근무표의 원래 근무.
  final DayDuty? original;
  final String? swapPostId;

  factory DayDuty.fromJson(Map<String, dynamic> j) => DayDuty(
        code: j['code'] as String? ?? '',
        type: _dutyTypeFrom(j['type'] as String?),
        turn: j['turn'] as String?,
        dayType: j['dayType'] as String?,
        turnKey: j['turnKey'] as String?,
        continues: j['continues'] as String?,
        original: j['original'] is Map<String, dynamic>
            ? DayDuty.fromJson(j['original'] as Map<String, dynamic>)
            : null,
        swapPostId: j['swapPostId'] as String?,
      );
}

class Driver {
  const Driver({required this.no, required this.name, required this.days, this.empNo});
  final int no;
  final String name;
  final String? empNo;
  final Map<String, DayDuty> days; // key: yyyy-MM-dd

  factory Driver.fromJson(Map<String, dynamic> j) {
    final rawDays = (j['days'] as Map<String, dynamic>? ?? {});
    return Driver(
      no: j['no'] as int? ?? 0,
      name: j['name'] as String? ?? '',
      empNo: j['empNo'] as String?,
      days: rawDays.map(
        (k, v) => MapEntry(k, DayDuty.fromJson(v as Map<String, dynamic>)),
      ),
    );
  }
}

/// "HH:MM" → 자정 기준 분. 형식이 아니면 null.
int? _minutes(String hhmm) {
  final m = RegExp(r'^(\d{1,2}):(\d{2})$').firstMatch(hhmm.trim());
  if (m == null) return null;
  return int.parse(m[1]!) * 60 + int.parse(m[2]!);
}

/// 행로표의 한 구간(운행·편승·대기·출고·입고·교대).
class TurnSegment {
  const TurnSegment({
    required this.kind,
    required this.train,
    required this.from,
    required this.to,
    required this.dep,
    required this.arr,
    this.dir,
    this.nextDay = false,
  });
  final String kind; // run|deadhead|standby|depot_out|depot_in|handover_in|handover_out
  final String train;
  final String from;
  final String to;
  final String dep;
  final String arr;
  final String? dir; // up|down|null
  final bool nextDay; // 교번 시작일 기준 자정 이후 출발

  static const _labels = {
    'run': '운행',
    'deadhead': '편승',
    'standby': '대기',
    'depot_out': '출고',
    'depot_in': '입고',
    'handover_in': '교대받음',
    'handover_out': '교대넘김',
  };
  String get kindLabel => _labels[kind] ?? kind;

  /// 열차가 실제로 출발하는 구간(다음 출발 안내용).
  bool get departs => kind == 'run' || kind == 'deadhead' || kind == 'depot_out';

  /// 교번 시작일 [date] 기준 실제 출발·도착 시각.
  (DateTime, DateTime)? timesOn(DateTime date) {
    final d = _minutes(dep), a = _minutes(arr);
    if (d == null || a == null) return null;
    final base = DateTime(date.year, date.month, date.day + (nextDay ? 1 : 0));
    final start = base.add(Duration(minutes: d));
    var end = base.add(Duration(minutes: a));
    if (end.isBefore(start)) end = end.add(const Duration(days: 1));
    return (start, end);
  }

  factory TurnSegment.fromJson(Map<String, dynamic> j) => TurnSegment(
        kind: j['kind'] as String? ?? '',
        train: j['train'] as String? ?? '',
        from: j['from'] as String? ?? '',
        to: j['to'] as String? ?? '',
        dep: j['dep'] as String? ?? '',
        arr: j['arr'] as String? ?? '',
        dir: j['dir'] as String?,
        nextDay: j['nextDay'] as bool? ?? false,
      );
}

class TurnDetail {
  const TurnDetail({
    required this.id,
    required this.type,
    required this.depart,
    required this.arrive,
    required this.firstRun,
    required this.brk,
    required this.route,
    this.trainNo,
    this.dayType,
    this.nextDay = false,
    this.workMinutes,
    this.driveMinutes,
    this.standbyMinutes,
    this.segments = const [],
    this.trainTimes = const [],
    this.diaImage,
  });
  final String id;
  final DutyType type;
  final String depart; // 출근
  final String arrive; // 퇴근
  final String firstRun;
  final String brk;
  final String route;
  final String? trainNo;
  final String? dayType; // 평평|평휴|휴평|휴휴
  final bool nextDay; // 퇴근이 다음날
  final int? workMinutes;
  final int? driveMinutes;
  final int? standbyMinutes;
  final List<TurnSegment> segments;
  final List<({String time, bool depot})> trainTimes;
  final String? diaImage;

  /// 교번 시작일 [date] 기준 출근·퇴근 시각. 시각이 없으면 null.
  (DateTime, DateTime)? timesOn(DateTime date) {
    final d = _minutes(depart), a = _minutes(arrive);
    if (d == null || a == null) return null;
    final base = DateTime(date.year, date.month, date.day);
    final start = base.add(Duration(minutes: d));
    var end = base.add(Duration(minutes: a));
    if (nextDay || !end.isAfter(start)) end = end.add(const Duration(days: 1));
    return (start, end);
  }

  factory TurnDetail.fromJson(Map<String, dynamic> j) => TurnDetail(
        id: j['id'] as String? ?? '',
        type: _dutyTypeFrom(j['type'] as String?),
        depart: j['depart'] as String? ?? '',
        arrive: j['arrive'] as String? ?? '',
        firstRun: j['firstRun'] as String? ?? '',
        brk: j['break'] as String? ?? '',
        route: j['route'] as String? ?? '',
        trainNo: j['trainNo'] as String?,
        dayType: j['dayType'] as String?,
        nextDay: j['nextDay'] as bool? ?? false,
        workMinutes: (j['workMinutes'] as num?)?.toInt(),
        driveMinutes: (j['driveMinutes'] as num?)?.toInt(),
        standbyMinutes: (j['standbyMinutes'] as num?)?.toInt(),
        segments: (j['segments'] as List? ?? [])
            .map((e) => TurnSegment.fromJson(e as Map<String, dynamic>))
            .toList(),
        trainTimes: (j['trainTimes'] as List? ?? []).map((e) {
          final time = e as Map<String, dynamic>;
          return (
            time: time['time'] as String? ?? '',
            depot: time['depot'] as bool? ?? false,
          );
        }).toList(),
        diaImage: j['diaImage'] as String?,
      );
}

class DutyMonth {
  const DutyMonth({
    required this.month,
    required this.line,
    required this.office,
    required this.dates,
    required this.drivers,
    required this.turns,
    required this.turnDetailIsDummy,
    this.offline = false,
    this.projected = false,
    this.projectedFrom,
  });
  final String month; // yyyy-MM
  final String line;
  final String office;
  final List<String> dates; // sorted yyyy-MM-dd
  final List<Driver> drivers;
  final Map<String, TurnDetail> turns;
  final bool turnDetailIsDummy;

  /// 서버 대신 기기에 저장해 둔 근무표를 보여주는 중.
  final bool offline;
  final bool projected;
  final String? projectedFrom;

  factory DutyMonth.fromJson(Map<String, dynamic> j, {bool offline = false}) => DutyMonth(
        month: j['month'] as String? ?? '',
        line: j['line'] as String? ?? '',
        office: j['office'] as String? ?? '',
        dates: (j['dates'] as List? ?? []).map((e) => e as String).toList(),
        drivers: (j['drivers'] as List? ?? [])
            .map((e) => Driver.fromJson(e as Map<String, dynamic>))
            .toList(),
        turns: (j['turns'] as Map<String, dynamic>? ?? {}).map(
          (k, v) => MapEntry(k, TurnDetail.fromJson(v as Map<String, dynamic>)),
        ),
        turnDetailIsDummy: j['turnDetailIsDummy'] as bool? ?? false,
        offline: offline,
        projected: j['projected'] as bool? ?? false,
        projectedFrom: j['projectedFrom'] as String?,
      );

  /// 로그인한 사용자의 이름과 같은 기관사. 없으면 null.
  Driver? driverNamed(String? name) =>
      drivers.where((d) => d.name == name).firstOrNull;

  /// (기관사, 날짜)의 실제 근무. 모든 화면이 이 함수로만 근무를 읽는다
  /// — 교번 변경 같은 덮어쓰기는 여기 한 곳에 적용하면 된다.
  DayDuty? dutyOn(Driver driver, String date) =>
      resolveDuty(this, driver, date, PersonalStore.instance.overrides(driver));

  /// 그날 근무의 행로표. turnKey가 없는 옛 데이터는 교번 id로 찾는다.
  TurnDetail? turnFor(DayDuty duty) => turns[duty.turnKey] ?? turns[duty.turn];

  /// 특정 날짜에 근무하는 기관사 목록(교번표용). turn이 있는 항목만, 출근 시각 순.
  List<({Driver driver, DayDuty duty})> assignmentsOn(String date) {
    final out = <({Driver driver, DayDuty duty})>[];
    for (final d in drivers) {
      final duty = dutyOn(d, date);
      if (duty != null && duty.turn != null) {
        out.add((driver: d, duty: duty));
      }
    }
    // 출근 시각을 모르는 교번은 뒤로.
    int key(DayDuty duty) => _minutes(turnFor(duty)?.depart ?? '') ?? 9999;
    out.sort((a, b) => key(a.duty).compareTo(key(b.duty)));
    return out;
  }
}

typedef DutySummary = ({int work, int day, int night, int standby, int off, int rest});

/// 한 달 근무 요약 (총 근무일 = 주간+야간+대기).
DutySummary dutySummary(DutyMonth m, Driver driver) {
  final types = m.dates.map((d) => m.dutyOn(driver, d)?.type).toList();
  int n(DutyType t) => types.where((x) => x == t).length;
  return (
    work: types.where((t) => t?.isWork ?? false).length,
    day: n(DutyType.day),
    night: n(DutyType.night),
    standby: n(DutyType.standby),
    off: n(DutyType.off),
    rest: n(DutyType.rest),
  );
}

enum DutyPhase { none, before, onDuty, done }

/// 지금 이 순간의 근무 상태. [dutyStatus]가 만든다.
class DutyStatus {
  const DutyStatus({
    required this.phase,
    this.today,
    this.turn,
    this.start,
    this.end,
    this.segment,
    this.nextDeparture,
  });
  final DutyPhase phase;
  final DayDuty? today;
  final TurnDetail? turn; // 진행 중이거나 오늘의 교번
  final DateTime? start; // 출근
  final DateTime? end; // 퇴근
  final TurnSegment? segment; // 근무 중 현재 구간. 구간 사이면 null
  final DateTime? nextDeparture;
}

/// [now] 기준 근무 상태(순수 함수). 전날 시작한 야간 교번이 아직 안 끝났으면 그 교번이 우선.
DutyStatus dutyStatus(DutyMonth m, Driver driver, DateTime now) {
  final day = DateTime(now.year, now.month, now.day);
  final yesterday = DateTime(now.year, now.month, now.day - 1);
  final today = m.dutyOn(driver, dutyDateKey(day));
  if (m.turnDetailIsDummy) return DutyStatus(phase: DutyPhase.none, today: today);

  DutyStatus at(TurnDetail turn, DateTime date, (DateTime, DateTime) times) {
    final (start, end) = times;
    if (now.isBefore(start)) {
      return DutyStatus(phase: DutyPhase.before, today: today, turn: turn, start: start, end: end);
    }
    if (!now.isBefore(end)) {
      return DutyStatus(phase: DutyPhase.done, today: today, turn: turn, start: start, end: end);
    }
    TurnSegment? current;
    DateTime? next;
    for (final seg in turn.segments) {
      final t = seg.timesOn(date);
      if (t == null) continue;
      if (current == null && !now.isBefore(t.$1) && now.isBefore(t.$2)) current = seg;
      if (next == null && seg.departs && t.$1.isAfter(now)) next = t.$1;
    }
    return DutyStatus(
      phase: DutyPhase.onDuty,
      today: today,
      turn: turn,
      start: start,
      end: end,
      segment: current,
      nextDeparture: next,
    );
  }

  // 1) 어젯밤 시작해 오늘 아침 끝나는 교번 ("70~")
  final prev = m.dutyOn(driver, dutyDateKey(yesterday));
  final carried = m.turns[today?.continues] ?? (prev == null ? null : m.turnFor(prev));
  final carriedTimes = carried?.timesOn(yesterday);
  DutyStatus? carriedDone;
  if (carried != null && carriedTimes != null && carriedTimes.$2.isAfter(day)) {
    final s = at(carried, yesterday, carriedTimes);
    if (s.phase == DutyPhase.onDuty) return s;
    carriedDone = s;
  }
  // 2) 오늘 시작하는 교번
  final turn = today == null ? null : m.turnFor(today);
  final times = turn?.timesOn(day);
  if (turn != null && times != null) return at(turn, day, times);
  return carriedDone ?? DutyStatus(phase: DutyPhase.none, today: today);
}

/// [dutyOn]의 본체(순수 함수). [overrides]: 날짜 → 사용자가 바꿔 넣은 근무 코드.
DayDuty? resolveDuty(DutyMonth m, Driver driver, String date, Map<String, String> overrides) {
  final base = driver.days[date];
  final d = DateTime.parse(date);
  final code = overrides[date];
  if (code == null) {
    // 전날 교번을 바꿨으면 "70~" 아침이 이어받는 교번도 따라간다.
    final prevDate = dutyDateKey(DateTime(d.year, d.month, d.day - 1));
    if (base?.continues == null || !overrides.containsKey(prevDate)) return base;
    final prev = resolveDuty(m, driver, prevDate, overrides);
    final prevTurn = prev == null ? null : m.turnFor(prev);
    return DayDuty(
      code: base!.code,
      type: base.type,
      dayType: base.dayType,
      continues: prevTurn != null && prevTurn.nextDay ? prev!.turnKey ?? prev.turn : null,
      original: base.original ?? base,
      swapPostId: base.swapPostId,
    );
  }
  String dayTypeOn(DateTime x) =>
      m.drivers.map((e) => e.days[dutyDateKey(x)]?.dayType).nonNulls.firstOrNull?.substring(0, 1) ??
      (x.weekday >= DateTime.saturday ? '휴' : '평');
  final dt = dayTypeOn(d);
  final n = RegExp(r'^\d+$').hasMatch(code) ? code : null;
  if (n != null) {
    // 주간은 "평평:5", 야간은 그날+다음날 조합 "평휴:61".
    final next = dayTypeOn(DateTime(d.year, d.month, d.day + 1));
    final key = ['$dt$dt:$n', '$dt$next:$n'].where(m.turns.containsKey).firstOrNull;
    final turn = m.turns[key] ?? m.turns[n];
    return DayDuty(
      code: code,
      type: turn?.type ?? (int.parse(n) >= 60 ? DutyType.night : DutyType.day),
      turn: n,
      dayType: dt,
      turnKey: key,
      original: base?.original ?? base,
      swapPostId: base?.swapPostId,
    );
  }
  final type = code.startsWith('대')
      ? DutyType.standby
      : code.startsWith('휴')
          ? DutyType.rest
          : code.startsWith('비') || code.endsWith('~')
              ? DutyType.off
              : DutyType.designated;
  return DayDuty(
    code: code,
    type: type,
    dayType: dt,
    original: base?.original ?? base,
    swapPostId: base?.swapPostId,
  );
}

/// 행로표에 없는 대기 근무 이름: 대N, N<60 주간 / N>=60 야간.
String standbyLabel(DayDuty d) {
  final n = int.tryParse(RegExp(r'\d+').firstMatch(d.code)?[0] ?? '');
  return n != null && n >= 60 ? '야간대기' : '주간대기';
}

/// 근무표 JSON의 날짜 키(yyyy-MM-dd).
String dutyDateKey(DateTime d) =>
    '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

/// 월별 근무표를 한 번만 읽어 캐싱한다. 받아 온 달은 기기에도 저장해 오프라인에 대비한다.
class DutyRepository {
  DutyRepository._();
  static final DutyRepository instance = DutyRepository._();

  static const _prefsPrefix = 'duty_month_';

  final Map<String, DutyMonth> _cache = {};
  final Map<String, Future<DutyMonth>> _loading = {};

  Future<List<String>> availableMonths() async {
    final client = AiApiClient();
    try {
      return (await client.fetchDutyMonths())..sort(); // 서버는 최신순으로 준다
    } catch (_) {
      // 오프라인: 기기에 저장해 둔 달만이라도 보여준다.
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs
          .getKeys()
          .where((k) => k.startsWith(_prefsPrefix))
          .map((k) => k.substring(_prefsPrefix.length))
          .toList()
        ..sort();
      if (saved.isEmpty) rethrow;
      return saved;
    } finally {
      client.close();
    }
  }

  Future<DutyMonth> load([String? month]) {
    final now = DateTime.now();
    final key = month ?? '${now.year}-${now.month.toString().padLeft(2, '0')}';
    if (_cache.containsKey(key)) return Future.value(_cache[key]);
    return _loading.putIfAbsent(key, () => _read(key));
  }

  Future<DutyMonth> _read(String month) async {
    final client = AiApiClient();
    final prefs = await SharedPreferences.getInstance();
    try {
      final json = await client.fetchDutyMonth(month);
      await prefs.setString('$_prefsPrefix$month', jsonEncode(json));
      return _cache[month] = DutyMonth.fromJson(json);
    } catch (_) {
      // 마지막으로 받은 근무표로 대신한다. 캐시하지 않으니 다음 load에서 다시 시도한다.
      final saved = prefs.getString('$_prefsPrefix$month');
      if (saved == null) rethrow;
      return DutyMonth.fromJson(jsonDecode(saved) as Map<String, dynamic>, offline: true);
    } finally {
      _loading.remove(month);
      client.close();
    }
  }

  void invalidate(String month) {
    _cache.remove(month);
    _loading.remove(month);
  }
}
