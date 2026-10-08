import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../core/duty_data.dart';
import '../core/personal_store.dart';

/// 행로표(교번 상세)를 바텀시트로 연다. [subtitle]은 날짜·기관사 등 맥락 한 줄.
Future<void> showTurnSheet(
  BuildContext context, {
  required TurnDetail turn,
  bool isDummy = false,
  String? subtitle,
}) {
  return showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: AppColors.card,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (_) => DraggableScrollableSheet(
      expand: false,
      initialChildSize: turn.segments.isEmpty || isDummy ? 0.5 : 0.75,
      maxChildSize: 0.95,
      builder: (context, controller) =>
          TurnSheet(turn: turn, isDummy: isDummy, subtitle: subtitle, controller: controller),
    ),
  );
}

/// 달력에서 고른 하루: 행로표(있으면) 또는 근무 안내 + 메모·교번 변경. 바꾸면 그 자리에서 다시 그린다.
Future<void> showDaySheet(
  BuildContext context, {
  required DutyMonth data,
  required Driver driver,
  required String date,
  required String subtitle,
}) {
  return showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: AppColors.card,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (_) => DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.75,
      maxChildSize: 0.95,
      builder: (context, controller) => ListenableBuilder(
        listenable: PersonalStore.instance,
        builder: (context, _) {
          final duty = data.dutyOn(driver, date);
          final turn = duty == null ? null : data.turnFor(duty) ?? data.turns[duty.continues];
          final footer = DayPersonalPanel(data: data, driver: driver, date: date, duty: duty);
          if (turn == null) {
            return _PlainDaySheet(duty: duty, subtitle: subtitle, controller: controller, footer: footer);
          }
          return TurnSheet(
            turn: turn,
            isDummy: data.turnDetailIsDummy,
            subtitle: duty!.continues != null && duty.turn == null ? '$subtitle · 전날 교번 이어서' : subtitle,
            controller: controller,
            footer: footer,
          );
        },
      ),
    ),
  );
}

/// "765" → "12시간 45분".
String formatMinutes(int? m) {
  if (m == null) return '-';
  if (m < 60) return '$m분';
  return m % 60 == 0 ? '${m ~/ 60}시간' : '${m ~/ 60}시간 ${m % 60}분';
}

class TurnSheet extends StatelessWidget {
  const TurnSheet({super.key, required this.turn, this.isDummy = false, this.subtitle, this.controller, this.footer});
  final TurnDetail turn;
  final bool isDummy;
  final String? subtitle;
  final ScrollController? controller;
  final Widget? footer; // 메모·교번 변경 패널

  @override
  Widget build(BuildContext context) {
    final c = dutyTypeColor(turn.type);
    return SafeArea(
      child: ListView(
        controller: controller,
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
        children: [
          Center(
            child: Container(
              width: 36,
              height: 4,
              decoration: BoxDecoration(color: AppColors.border, borderRadius: BorderRadius.circular(2)),
            ),
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 8,
            runSpacing: 6,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              Text('교번 ${turn.id}', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
              if (turn.dayType != null) _Badge(turn.dayType!, AppColors.line6),
              _Badge(turn.type.label, c),
            ],
          ),
          if (subtitle != null) ...[
            const SizedBox(height: 4),
            Text(subtitle!, style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)),
          ],
          const SizedBox(height: 16),
          if (isDummy)
            const _Notice('교번별 출무 시각·구간은 아직 연결되지 않았습니다.')
          else ...[
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _Fact('출근', turn.depart),
                _Fact('퇴근', turn.nextDay ? '${turn.arrive} (익일)' : turn.arrive),
                _Fact('근무시간', formatMinutes(turn.workMinutes)),
                _Fact('운전', formatMinutes(turn.driveMinutes)),
                _Fact('대기', formatMinutes(turn.standbyMinutes)),
              ],
            ),
            if (turn.route.isNotEmpty) ...[
              const SizedBox(height: 12),
              Row(children: [
                const Icon(Icons.route_rounded, size: 18, color: AppColors.line6),
                const SizedBox(width: 8),
                Expanded(child: Text(turn.route, style: const TextStyle(fontWeight: FontWeight.w700))),
              ]),
            ],
            const SizedBox(height: 18),
            if (turn.segments.isEmpty)
              const _Notice('상세 행로 정보가 없습니다.')
            else
              for (var i = 0; i < turn.segments.length; i++)
                _SegmentRow(seg: turn.segments[i], last: i == turn.segments.length - 1),
          ],
          ?footer,
        ],
      ),
    );
  }
}

class _SegmentRow extends StatelessWidget {
  const _SegmentRow({required this.seg, required this.last});
  final TurnSegment seg;
  final bool last;

  @override
  Widget build(BuildContext context) {
    final isRun = seg.kind == 'run';
    final accent = seg.kind == 'standby' ? AppColors.ghostText : AppColors.line6;
    final dir = switch (seg.dir) { 'up' => '▲ 상선', 'down' => '▼ 하선', _ => null };
    final time = seg.dep == seg.arr ? seg.dep : '${seg.dep}–${seg.arr}';
    final place = seg.from == seg.to ? seg.from : '${seg.from} → ${seg.to}';
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SizedBox(
            width: 20,
            child: Column(children: [
              const SizedBox(height: 4),
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: isRun ? accent : AppColors.card,
                  shape: BoxShape.circle,
                  border: Border.all(color: accent, width: 2),
                ),
              ),
              if (!last) Expanded(child: Container(width: 2, color: AppColors.line6.withValues(alpha: 0.35))),
            ]),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Wrap(
                    spacing: 6,
                    runSpacing: 4,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      Text(time, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
                      if (seg.nextDay) Text('익일', style: TextStyle(fontSize: 12, color: AppColors.secondaryInk)),
                      if (dir != null)
                        Text(dir, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.line6)),
                      if (!isRun) _Badge(seg.kindLabel, accent),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    seg.train.isEmpty ? place : '${seg.train}열차 · $place',
                    style: TextStyle(fontSize: 14, color: AppColors.secondaryInk),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Fact extends StatelessWidget {
  const _Fact(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.canvas,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label, style: TextStyle(fontSize: 12, color: AppColors.secondaryInk)),
          Text(value.isEmpty ? '-' : value, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800)),
        ],
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge(this.text, this.color);
  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(8)),
      child: Text(text, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: color)),
    );
  }
}

class _Notice extends StatelessWidget {
  const _Notice(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: AppColors.softEvidence, borderRadius: BorderRadius.circular(10)),
      child: Text(text, style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)),
    );
  }
}

/// 행로표가 없는 날(비번·휴무·대기 등)의 시트.
class _PlainDaySheet extends StatelessWidget {
  const _PlainDaySheet({required this.duty, required this.subtitle, required this.controller, required this.footer});
  final DayDuty? duty;
  final String subtitle;
  final ScrollController controller;
  final Widget footer;

  @override
  Widget build(BuildContext context) {
    final d = duty;
    final standby = d?.type == DutyType.standby;
    return SafeArea(
      child: ListView(
        controller: controller,
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
        children: [
          Center(
            child: Container(
              width: 36,
              height: 4,
              decoration: BoxDecoration(color: AppColors.border, borderRadius: BorderRadius.circular(2)),
            ),
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 8,
            runSpacing: 6,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              Text(d == null ? '근무 정보 없음' : (standby ? standbyLabel(d) : d.code),
                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
              if (d != null) _Badge(standby ? d.code : d.type.label, dutyTypeColor(d.type)),
            ],
          ),
          const SizedBox(height: 4),
          Text(subtitle, style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)),
          if (standby) ...[
            const SizedBox(height: 16),
            const _Notice('충당여부 및 출근시각 확인'),
          ],
          footer,
        ],
      ),
    );
  }
}

/// 날짜별 메모와 교번 변경(기기에만 저장).
class DayPersonalPanel extends StatelessWidget {
  const DayPersonalPanel({super.key, required this.data, required this.driver, required this.date, required this.duty});
  final DutyMonth data;
  final Driver driver;
  final String date;
  final DayDuty? duty;

  Future<String?> _prompt(BuildContext context, String title, String initial, {int maxLines = 1}) {
    final c = TextEditingController(text: initial);
    return showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: c,
          autofocus: true,
          maxLines: maxLines,
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('취소')),
          FilledButton(onPressed: () => Navigator.pop(context, c.text), child: const Text('저장')),
        ],
      ),
    );
  }

  /// 고를 수 있는 근무 코드: 행로표 교번 번호 + 이 달 근무표에 나온 코드. 숫자 먼저.
  List<String> _codes() {
    final codes = {
      for (final k in data.turns.keys) k.split(':').last,
      for (final d in data.drivers) for (final x in d.days.values) if (x.code.isNotEmpty) x.code,
    }.toList();
    int? n(String c) => int.tryParse(c);
    codes.sort((a, b) => switch ((n(a), n(b))) {
          (int x, int y) => x.compareTo(y),
          (int _, null) => -1,
          (null, int _) => 1,
          _ => a.compareTo(b),
        });
    return codes;
  }

  /// iOS식 휠 선택. 저장하면 고른 코드, 취소하면 null.
  Future<String?> _pick(BuildContext context, String? initial) {
    final codes = _codes();
    if (codes.isEmpty) return Future.value();
    var i = initial == null ? 0 : codes.indexOf(initial).clamp(0, codes.length - 1);
    return showCupertinoModalPopup<String>(
      context: context,
      builder: (context) => Container(
        height: 300,
        color: AppColors.card,
        child: SafeArea(
          top: false,
          child: Column(children: [
            Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              CupertinoButton(onPressed: () => Navigator.pop(context), child: const Text('취소')),
              const Text('교번 변경', style: TextStyle(fontWeight: FontWeight.w800)),
              CupertinoButton(onPressed: () => Navigator.pop(context, codes[i]), child: const Text('저장')),
            ]),
            Expanded(
              child: CupertinoPicker(
                itemExtent: 40,
                scrollController: FixedExtentScrollController(initialItem: i),
                onSelectedItemChanged: (v) => i = v,
                children: [for (final c in codes) Center(child: Text(c))],
              ),
            ),
          ]),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final store = PersonalStore.instance;
    final memo = store.memo(driver, date);
    final original = duty?.original;
    final overridden = store.overrides(driver).containsKey(date);
    final label = TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.secondaryInk);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 8),
        Divider(color: AppColors.border),
        const SizedBox(height: 8),
        Text('교번 변경', style: label),
        const SizedBox(height: 4),
        if (overridden) ...[
          Text('변경 (원래: ${original == null || original.code.isEmpty ? '-' : original.code})',
              style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.line6)),
          TextButton.icon(
            onPressed: () => store.setOverride(driver, date, null),
            icon: const Icon(Icons.undo_rounded, size: 16),
            label: const Text('원래 교번으로 되돌리기'),
          ),
        ],
        OutlinedButton.icon(
          onPressed: () async {
            final code = await _pick(context, duty?.code);
            if (code != null) await store.setOverride(driver, date, code);
          },
          icon: const Icon(Icons.swap_horiz_rounded, size: 18),
          label: Text(overridden ? '다시 변경' : '바꾼 교번 선택'),
        ),
        const SizedBox(height: 16),
        Text('메모', style: label),
        const SizedBox(height: 4),
        Text(memo ?? '메모 없음', style: TextStyle(color: memo == null ? AppColors.ghostText : AppColors.ink)),
        TextButton.icon(
          onPressed: () async {
            final text = await _prompt(context, '메모', memo ?? '', maxLines: 4);
            if (text != null) await store.setMemo(driver, date, text);
          },
          icon: const Icon(Icons.edit_note_rounded, size: 18),
          label: Text(memo == null ? '메모 쓰기' : '메모 수정'),
        ),
      ],
    );
  }
}
