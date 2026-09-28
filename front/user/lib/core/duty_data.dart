import 'dart:convert';
import 'package:flutter/services.dart' show rootBundle;

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
  const DayDuty({required this.code, required this.type, this.turn});
  final String code;
  final DutyType type;
  final String? turn;

  factory DayDuty.fromJson(Map<String, dynamic> j) => DayDuty(
        code: j['code'] as String? ?? '',
        type: _dutyTypeFrom(j['type'] as String?),
        turn: j['turn'] as String?,
      );
}

class Driver {
  const Driver({required this.no, required this.name, required this.days});
  final int no;
  final String name;
  final Map<String, DayDuty> days; // key: yyyy-MM-dd

  factory Driver.fromJson(Map<String, dynamic> j) {
    final rawDays = (j['days'] as Map<String, dynamic>? ?? {});
    return Driver(
      no: j['no'] as int? ?? 0,
      name: j['name'] as String? ?? '',
      days: rawDays.map(
        (k, v) => MapEntry(k, DayDuty.fromJson(v as Map<String, dynamic>)),
      ),
    );
  }
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
  });
  final String id;
  final DutyType type;
  final String depart;
  final String arrive;
  final String firstRun;
  final String brk;
  final String route;
  final String? trainNo;

  factory TurnDetail.fromJson(Map<String, dynamic> j) => TurnDetail(
        id: j['id'] as String? ?? '',
        type: _dutyTypeFrom(j['type'] as String?),
        depart: j['depart'] as String? ?? '',
        arrive: j['arrive'] as String? ?? '',
        firstRun: j['firstRun'] as String? ?? '',
        brk: j['break'] as String? ?? '',
        route: j['route'] as String? ?? '',
        trainNo: j['trainNo'] as String?,
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
  });
  final String month; // yyyy-MM
  final String line;
  final String office;
  final List<String> dates; // sorted yyyy-MM-dd
  final List<Driver> drivers;
  final Map<String, TurnDetail> turns;
  final bool turnDetailIsDummy;

  factory DutyMonth.fromJson(Map<String, dynamic> j) => DutyMonth(
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
      );

  /// 특정 날짜에 근무하는 기관사 목록(교번표용). turn이 있는 항목만.
  List<({Driver driver, DayDuty duty})> assignmentsOn(String date) {
    final out = <({Driver driver, DayDuty duty})>[];
    for (final d in drivers) {
      final duty = d.days[date];
      if (duty != null && duty.turn != null) {
        out.add((driver: d, duty: duty));
      }
    }
    out.sort((a, b) {
      final ta = turns[a.duty.turn]?.depart ?? '';
      final tb = turns[b.duty.turn]?.depart ?? '';
      return ta.compareTo(tb);
    });
    return out;
  }
}

/// 자산 JSON을 한 번만 읽어 캐싱한다.
class DutyRepository {
  DutyRepository._();
  static final DutyRepository instance = DutyRepository._();

  DutyMonth? _cache;
  Future<DutyMonth>? _loading;

  Future<DutyMonth> load() {
    if (_cache != null) return Future.value(_cache);
    return _loading ??= _read();
  }

  Future<DutyMonth> _read() async {
    final raw = await rootBundle.loadString('assets/data/duty_2026_06.json');
    final json = jsonDecode(raw) as Map<String, dynamic>;
    final parsed = DutyMonth.fromJson(json);
    _cache = parsed;
    return parsed;
  }
}
