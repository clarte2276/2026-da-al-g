import 'dart:async';

import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../core/duty_data.dart';
import '../core/personal_store.dart';
import '../services/auth_session.dart';
import 'status_pill.dart';
import 'turn_sheet.dart';

/// 시간대별 인사.
String dutyGreeting(DateTime now) {
  final h = now.hour;
  if (h >= 5 && h < 11) return '좋은 아침이에요';
  if (h >= 11 && h < 14) return '점심은 챙기셨나요';
  if (h >= 14 && h < 18) return '좋은 오후예요';
  if (h >= 18 && h < 22) return '좋은 저녁이에요';
  return '늦은 시간까지 수고 많으세요';
}

String _hm(DateTime t) => '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';

/// "2시간 14분 후" (분 단위 올림).
String _until(DateTime from, DateTime to) {
  final m = (to.difference(from).inSeconds + 59) ~/ 60;
  if (m < 60) return '$m분 후';
  return m % 60 == 0 ? '${m ~/ 60}시간 후' : '${m ~/ 60}시간 ${m % 60}분 후';
}

/// 근무 상태 → (제목, 보조 문구). [now]를 받아 테스트할 수 있게 순수 함수로 둔다.
(String, String) describeDutyStatus(DutyStatus s, DateTime now) {
  final turn = s.turn;
  switch (s.phase) {
    case DutyPhase.before:
      return ('${turn!.type.label} · 교번 ${turn.id}', '오늘 출근 ${_hm(s.start!)} · ${_until(now, s.start!)}');
    case DutyPhase.onDuty:
      final seg = s.segment;
      final title = seg == null || seg.kind == 'standby'
          ? '대기 중'
          : '${seg.kind == 'deadhead' ? '편승 중' : '운행 중'} · ${seg.train}열차 ${seg.from}→${seg.to}';
      final next = s.nextDeparture;
      final meta = next == null
          ? '퇴근 ${_hm(s.end!)}'
          : '다음 출발 ${_hm(next)} (약 ${_until(now, next)}) · 퇴근 ${_hm(s.end!)}';
      return (title, meta);
    case DutyPhase.done:
      return ('오늘 근무 끝났어요', '수고하셨어요 · 퇴근 ${_hm(s.end!)}');
    case DutyPhase.none:
      final today = s.today;
      if (today == null) return ('오늘 근무 정보가 없습니다', '');
      switch (today.type) {
        case DutyType.rest:
          return ('오늘은 휴무예요', '푹 쉬세요');
        case DutyType.off:
          return ('오늘은 비번이에요', '푹 쉬세요');
        case DutyType.designated:
          return ('오늘은 지정 근무예요', today.code);
        case DutyType.standby:
          return ('${standbyLabel(today)} · ${today.code}', '충당여부 및 출근시각 확인');
        default:
          final no = today.turn == null ? '' : ' · 교번 ${today.turn}';
          return ('${today.type.label}$no', '출근 시각 정보가 아직 없어요');
      }
  }
}

/// 홈의 "오늘의 근무" 카드. 30초마다 다시 그려 지금 운행 중인 구간을 따라간다.
class TodayDutyCard extends StatefulWidget {
  const TodayDutyCard({super.key, this.onTap});
  final VoidCallback? onTap;

  @override
  State<TodayDutyCard> createState() => _TodayDutyCardState();
}

class _TodayDutyCardState extends State<TodayDutyCard> {
  static const _weekdays = ['월', '화', '수', '목', '금', '토', '일'];
  final Future<DutyMonth> _future = DutyRepository.instance.load();
  late final Timer _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 30), (_) => _refresh());
    PersonalStore.instance.addListener(_refresh); // 교번 변경 반영
  }

  void _refresh() => setState(() {});

  @override
  void dispose() {
    _timer.cancel();
    PersonalStore.instance.removeListener(_refresh);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    return GestureDetector(
      onTap: widget.onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: AppColors.dutyCardBg,
          borderRadius: BorderRadius.circular(18),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Wrap(
                    spacing: 8,
                    runSpacing: 6,
                    children: [
                      const StatusPill(label: '오늘의 근무', color: Colors.white, bgColor: Color(0xff3d3d3d)),
                      StatusPill(
                        label: '${now.month}/${now.day} (${_weekdays[now.weekday - 1]})',
                        color: AppColors.line6,
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.arrow_forward_ios_rounded, size: 14, color: Colors.white54),
              ],
            ),
            const SizedBox(height: 16),
            FutureBuilder<DutyMonth>(
              future: _future,
              builder: (context, snap) => _body(context, snap, now),
            ),
          ],
        ),
      ),
    );
  }

  Widget _body(BuildContext context, AsyncSnapshot<DutyMonth> snap, DateTime now) {
    final name = AuthSession.current?.user.name;
    final greeting = name == null ? dutyGreeting(now) : '${dutyGreeting(now)}, $name 기관사님';
    final data = snap.data;
    final me = data?.driverNamed(name);
    final String title, meta;
    DutyStatus? status;
    if (snap.hasError) {
      (title, meta) = ('근무표를 불러오지 못했습니다', '근무 탭에서 다시 확인하세요');
    } else if (data == null) {
      (title, meta) = ('불러오는 중…', '');
    } else if (me == null) {
      (title, meta) = ('근무표에서 내 이름을 찾지 못했습니다', '근무 탭에서 기관사를 선택해 확인하세요');
    } else {
      status = dutyStatus(data, me, now);
      (title, meta) = describeDutyStatus(status, now);
    }
    final tomorrow = data == null || me == null
        ? null
        : data.dutyOn(me, dutyDateKey(DateTime(now.year, now.month, now.day + 1)));
    final sheetTurn = status?.turn ?? (status?.today == null ? null : data!.turnFor(status!.today!));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(greeting, style: TextStyle(color: AppColors.dutyMeta, fontSize: 14)),
        const SizedBox(height: 6),
        Text(title, style: const TextStyle(color: Colors.white, fontSize: 19, fontWeight: FontWeight.w700)),
        if (meta.isNotEmpty) ...[
          const SizedBox(height: 8),
          Text(meta, style: TextStyle(color: AppColors.dutyMeta, fontSize: 14)),
        ],
        if (tomorrow != null) ...[
          const SizedBox(height: 14),
          Text('내일  ${_tomorrowText(data!, tomorrow)}',
              style: const TextStyle(color: Colors.white70, fontSize: 14, fontWeight: FontWeight.w600)),
        ],
        if (data?.offline ?? false) ...[
          const SizedBox(height: 8),
          const Text('오프라인 · 저장된 근무표', style: TextStyle(color: Colors.white54, fontSize: 13)),
        ],
        if (sheetTurn != null && !data!.turnDetailIsDummy) ...[
          const SizedBox(height: 14),
          OutlinedButton.icon(
            onPressed: () => showTurnSheet(context, turn: sheetTurn, subtitle: '${me!.name} · 오늘'),
            icon: const Icon(Icons.timeline_rounded, size: 18),
            label: const Text('행로표 보기'),
            style: OutlinedButton.styleFrom(
              foregroundColor: Colors.white,
              side: const BorderSide(color: AppColors.line6),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(99)),
            ),
          ),
        ],
      ],
    );
  }

  String _tomorrowText(DutyMonth data, DayDuty duty) {
    final turn = data.turnFor(duty);
    final depart = turn == null || data.turnDetailIsDummy || turn.depart.isEmpty ? '' : ' · 출근 ${turn.depart}';
    return '${duty.type.label} ${duty.code}$depart';
  }
}
