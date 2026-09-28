import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../core/duty_data.dart';
import '../services/auth_session.dart';
import '../widgets/skeleton.dart';

/// 근무계획 엑셀(파싱된 JSON) 기반의 dia5형 뷰어.
/// - 근무 달력: 선택한 기관사의 월간 근무(주/야/비/휴/대)
/// - 교번표: 일자별 근무 교번 목록 + 상세(시각·구간)
class DutyBoardScreen extends StatefulWidget {
  const DutyBoardScreen({super.key});

  @override
  State<DutyBoardScreen> createState() => _DutyBoardScreenState();
}

enum _Mode { calendar, turns }

class _DutyBoardScreenState extends State<DutyBoardScreen> {
  final _future = DutyRepository.instance.load();
  _Mode _mode = _Mode.calendar;
  Driver? _driver;
  String? _selectedDate;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(
        title: const Text('근무 · 교번', style: TextStyle(fontSize: 16)),
      ),
      body: FutureBuilder<DutyMonth>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const _CalendarSkeleton();
          }
          if (snap.hasError) {
            return Center(child: Text('근무 데이터를 불러오지 못했습니다.\n${snap.error}'));
          }
          final data = snap.data!;
          _driver ??= data.driverNamed(AuthSession.current?.user.name) ??
              data.drivers.first;
          _selectedDate ??= data.dates.first;
          return Column(
            children: [
              _Header(
                data: data,
                driver: _driver!,
                onPickDriver: () => _pickDriver(data),
              ),
              _ModeSwitch(mode: _mode, onChanged: (m) => setState(() => _mode = m)),
              Expanded(
                child: _mode == _Mode.calendar
                    ? _CalendarView(
                        data: data,
                        driver: _driver!,
                        onTapWork: (turn) => _showTurn(data, turn),
                      )
                    : _TurnsView(
                        data: data,
                        selectedDate: _selectedDate!,
                        onDateChanged: (d) => setState(() => _selectedDate = d),
                        onTapTurn: (turn) => _showTurn(data, turn),
                      ),
              ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _pickDriver(DutyMonth data) async {
    final picked = await showModalBottomSheet<Driver>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.canvas,
      builder: (_) => _DriverPicker(drivers: data.drivers, current: _driver),
    );
    if (picked != null) setState(() => _driver = picked);
  }

  void _showTurn(DutyMonth data, String turnId) {
    final turn = data.turns[turnId];
    if (turn == null) return;
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.card,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _TurnDetailSheet(turn: turn, isDummy: data.turnDetailIsDummy),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.data, required this.driver, required this.onPickDriver});
  final DutyMonth data;
  final Driver driver;
  final VoidCallback onPickDriver;

  @override
  Widget build(BuildContext context) {
    final ym = data.month.split('-');
    return Container(
      width: double.infinity,
      color: AppColors.card,
      padding: const EdgeInsets.fromLTRB(20, 12, 16, 14),
      child: Wrap(
        alignment: WrapAlignment.spaceBetween,
        crossAxisAlignment: WrapCrossAlignment.center,
        spacing: 8,
        runSpacing: 8,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('${data.office} · ${data.line}',
                  style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)),
              const SizedBox(height: 2),
              Text('${ym[0]}년 ${int.parse(ym[1])}월 근무계획',
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
            ],
          ),
          OutlinedButton.icon(
            onPressed: onPickDriver,
            icon: const Icon(Icons.person_outline_rounded, size: 18),
            label: Text('${driver.no} ${driver.name}'),
            style: OutlinedButton.styleFrom(
              foregroundColor: AppColors.ink,
              side: BorderSide(color: AppColors.border),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(99)),
            ),
          ),
        ],
      ),
    );
  }
}

class _ModeSwitch extends StatelessWidget {
  const _ModeSwitch({required this.mode, required this.onChanged});
  final _Mode mode;
  final ValueChanged<_Mode> onChanged;

  @override
  Widget build(BuildContext context) {
    Widget tab(String label, _Mode m) => Expanded(
          child: GestureDetector(
            onTap: () => onChanged(m),
            child: Container(
              margin: const EdgeInsets.all(4),
              padding: const EdgeInsets.symmetric(vertical: 9),
              decoration: BoxDecoration(
                color: mode == m ? AppColors.line6GoldDeep : Colors.transparent,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(label,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: mode == m ? Colors.white : AppColors.ink,
                    fontWeight: FontWeight.w700,
                  )),
            ),
          ),
        );
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 12, 16, 4),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(children: [tab('근무 달력', _Mode.calendar), tab('교번표', _Mode.turns)]),
    );
  }
}

/// 월간 근무 달력 (선택 기관사)
class _CalendarView extends StatelessWidget {
  const _CalendarView({required this.data, required this.driver, required this.onTapWork});
  final DutyMonth data;
  final Driver driver;
  final ValueChanged<String> onTapWork;

  @override
  Widget build(BuildContext context) {
    final first = DateTime.parse(data.dates.first);
    final leading = first.weekday % 7; // Sun=0
    const wd = ['일', '월', '화', '수', '목', '금', '토'];

    final cells = <Widget>[];
    for (var i = 0; i < leading; i++) {
      cells.add(const SizedBox.shrink());
    }
    for (final date in data.dates) {
      final duty = driver.days[date];
      final day = int.parse(date.split('-')[2]);
      final type = duty?.type ?? DutyType.unknown;
      final color = dutyTypeColor(type);
      cells.add(GestureDetector(
        onTap: (duty?.turn != null) ? () => onTapWork(duty!.turn!) : null,
        child: Container(
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: color.withValues(alpha: 0.4)),
          ),
          padding: const EdgeInsets.symmetric(vertical: 6),
          child: FittedBox(
            fit: BoxFit.scaleDown,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('$day', style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)),
                const SizedBox(height: 2),
                Text(duty?.code ?? '', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: color)),
              ],
            ),
          ),
        ),
      ));
    }

    // monthly stats
    int count(DutyType t) => driver.days.values.where((d) => d.type == t).length;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: wd
              .map((w) => Expanded(
                  child: Center(
                      child: Text(w, style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)))))
              .toList(),
        ),
        const SizedBox(height: 8),
        GridView.count(
          crossAxisCount: 7,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          mainAxisSpacing: 6,
          crossAxisSpacing: 6,
          childAspectRatio: 0.82,
          children: cells,
        ),
        const SizedBox(height: 16),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            _Stat('주간', count(DutyType.day), DutyType.day),
            _Stat('야간', count(DutyType.night), DutyType.night),
            _Stat('대기', count(DutyType.standby), DutyType.standby),
            _Stat('비번', count(DutyType.off), DutyType.off),
            _Stat('휴무', count(DutyType.rest), DutyType.rest),
          ],
        ),
        const SizedBox(height: 8),
        Text('주간·야간·대기 셀을 누르면 교번 상세가 열립니다.',
            style: TextStyle(fontSize: 13, color: AppColors.ghostText)),
      ],
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat(this.label, this.value, this.type);
  final String label;
  final int value;
  final DutyType type;

  @override
  Widget build(BuildContext context) {
    final c = dutyTypeColor(type);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: c.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Text(label, style: TextStyle(fontSize: 13, color: c, fontWeight: FontWeight.w700)),
        const SizedBox(width: 6),
        Text('$value', style: TextStyle(fontSize: 14, color: c, fontWeight: FontWeight.w900)),
      ]),
    );
  }
}

/// 일자별 교번표
class _TurnsView extends StatelessWidget {
  const _TurnsView({
    required this.data,
    required this.selectedDate,
    required this.onDateChanged,
    required this.onTapTurn,
  });
  final DutyMonth data;
  final String selectedDate;
  final ValueChanged<String> onDateChanged;
  final ValueChanged<String> onTapTurn;

  @override
  Widget build(BuildContext context) {
    final assignments = data.assignmentsOn(selectedDate);
    final day = assignments.where((a) => a.duty.type == DutyType.day).length;
    final night = assignments.where((a) => a.duty.type == DutyType.night).length;
    final standby = assignments.where((a) => a.duty.type == DutyType.standby).length;

    return Column(
      children: [
        SizedBox(
          height: 64,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            itemCount: data.dates.length,
            separatorBuilder: (_, _) => const SizedBox(width: 8),
            itemBuilder: (_, i) {
              final d = data.dates[i];
              final dt = DateTime.parse(d);
              const wd = ['월', '화', '수', '목', '금', '토', '일'];
              final sel = d == selectedDate;
              return GestureDetector(
                onTap: () => onDateChanged(d),
                child: Container(
                  width: 46,
                  decoration: BoxDecoration(
                    color: sel ? AppColors.line6GoldDeep : AppColors.card,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: sel ? AppColors.line6GoldDeep : AppColors.border),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(wd[dt.weekday - 1],
                          style: TextStyle(fontSize: 13, color: sel ? Colors.white70 : AppColors.secondaryInk)),
                      Text('${dt.day}',
                          style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w800,
                              color: sel ? Colors.white : AppColors.ink)),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          child: Row(children: [
            _Pill('전체 ${assignments.length}', AppColors.ink),
            const SizedBox(width: 6),
            _Pill('주간 $day', dutyTypeColor(DutyType.day)),
            const SizedBox(width: 6),
            _Pill('야간 $night', dutyTypeColor(DutyType.night)),
            const SizedBox(width: 6),
            _Pill('대기 $standby', dutyTypeColor(DutyType.standby)),
          ]),
        ),
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            itemCount: assignments.length,
            separatorBuilder: (_, _) => const SizedBox(height: 8),
            itemBuilder: (_, i) {
              final a = assignments[i];
              final turn = data.turns[a.duty.turn];
              final c = dutyTypeColor(a.duty.type);
              return GestureDetector(
                onTap: () => onTapTurn(a.duty.turn!),
                child: Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.card,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 44,
                        height: 44,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          color: c.withValues(alpha: 0.14),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(a.duty.turn!,
                            style: TextStyle(fontWeight: FontWeight.w900, color: c)),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(a.driver.name,
                                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
                            const SizedBox(height: 2),
                            Text(turn == null || data.turnDetailIsDummy ? a.duty.type.label : '${a.duty.type.label} · ${turn.route}',
                                style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)),
                          ],
                        ),
                      ),
                      Text(turn == null || data.turnDetailIsDummy ? '' : '${turn.depart}~${turn.arrive}',
                          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill(this.text, this.color);
  final String text;
  final Color color;
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(99),
      ),
      child: Text(text, style: TextStyle(fontSize: 13, color: color, fontWeight: FontWeight.w700)),
    );
  }
}

class _TurnDetailSheet extends StatelessWidget {
  const _TurnDetailSheet({required this.turn, required this.isDummy});
  final TurnDetail turn;
  final bool isDummy;

  @override
  Widget build(BuildContext context) {
    final c = dutyTypeColor(turn.type);
    Widget row(IconData ic, String k, String v) => Padding(
          padding: const EdgeInsets.symmetric(vertical: 6),
          child: Row(children: [
            Icon(ic, size: 18, color: AppColors.secondaryInk),
            const SizedBox(width: 10),
            Text(k, style: TextStyle(color: AppColors.secondaryInk)),
            const Spacer(),
            Text(v, style: const TextStyle(fontWeight: FontWeight.w700)),
          ]),
        );
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(color: c.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(10)),
                child: Text('교번 ${turn.id}', style: TextStyle(fontWeight: FontWeight.w900, color: c)),
              ),
              const SizedBox(width: 8),
              Text(turn.type.label, style: TextStyle(color: c, fontWeight: FontWeight.w700)),
            ]),
            const SizedBox(height: 14),
            if (!isDummy) ...[
              row(Icons.route_rounded, '구간', turn.route),
              row(Icons.login_rounded, '출무', turn.depart),
              row(Icons.train_rounded, '첫 출발', turn.firstRun),
              row(Icons.logout_rounded, '근무 종료', turn.arrive),
              row(Icons.coffee_rounded, '휴게', turn.brk),
              if (turn.trainNo != null) row(Icons.confirmation_number_outlined, '열차번호', turn.trainNo!),
            ] else ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.softEvidence,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  '교번별 출무 시각·구간은 아직 연결되지 않았습니다.',
                  style: TextStyle(fontSize: 13, color: AppColors.secondaryInk),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _DriverPicker extends StatefulWidget {
  const _DriverPicker({required this.drivers, required this.current});
  final List<Driver> drivers;
  final Driver? current;

  @override
  State<_DriverPicker> createState() => _DriverPickerState();
}

class _DriverPickerState extends State<_DriverPicker> {
  String _q = '';
  @override
  Widget build(BuildContext context) {
    final filtered = widget.drivers
        .where((d) => _q.isEmpty || d.name.contains(_q) || '${d.no}'.contains(_q))
        .toList();
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: SizedBox(
        height: MediaQuery.of(context).size.height * 0.7,
        child: Column(
          children: [
            const SizedBox(height: 12),
            const Text('기관사 선택', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
            Padding(
              padding: const EdgeInsets.all(16),
              child: TextField(
                autofocus: false,
                onChanged: (v) => setState(() => _q = v),
                decoration: InputDecoration(
                  hintText: '이름 또는 연번 검색',
                  prefixIcon: const Icon(Icons.search_rounded),
                  filled: true,
                  fillColor: AppColors.card,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(color: AppColors.border),
                  ),
                ),
              ),
            ),
            Expanded(
              child: ListView.builder(
                itemCount: filtered.length,
                itemBuilder: (_, i) {
                  final d = filtered[i];
                  final sel = d.no == widget.current?.no;
                  return ListTile(
                    leading: CircleAvatar(
                      backgroundColor: AppColors.softEvidence,
                      child: Text('${d.no}', style: TextStyle(fontSize: 13, color: AppColors.evidence)),
                    ),
                    title: Text(d.name),
                    trailing: sel ? const Icon(Icons.check_rounded, color: AppColors.line6Gold) : null,
                    onTap: () => Navigator.pop(context, d),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// 로딩 중 달력 자리를 대신하는 스켈레톤.
class _CalendarSkeleton extends StatelessWidget {
  const _CalendarSkeleton();

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: List.generate(
            7,
            (_) => const Expanded(
              child: Center(child: SkeletonBox(width: 24, height: 12)),
            ),
          ),
        ),
        const SizedBox(height: 8),
        GridView.count(
          crossAxisCount: 7,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          mainAxisSpacing: 6,
          crossAxisSpacing: 6,
          childAspectRatio: 0.82,
          children: List.generate(35, (_) => const SkeletonBox(borderRadius: 10)),
        ),
        const SizedBox(height: 16),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: List.generate(
            5,
            (_) => const SkeletonBox(width: 64, height: 34, borderRadius: 10),
          ),
        ),
      ],
    );
  }
}
