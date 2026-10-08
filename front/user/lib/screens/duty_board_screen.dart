import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../core/duty_data.dart';
import '../core/personal_store.dart';
import '../services/auth_session.dart';
import '../widgets/offline_banner.dart';
import '../widgets/skeleton.dart';
import '../widgets/turn_sheet.dart';
import 'compare_screen.dart';
import 'exchange_screen.dart';
import 'roster_screen.dart';
import 'standby_coverage_screen.dart';

/// 근무계획 엑셀(파싱된 JSON) 기반의 기관사 근무 뷰어.
/// - 근무 달력: 선택한 기관사의 월간 근무(주/야/비/휴/대) + 근무 요약
/// - 교번표: 일자별 근무 교번 목록(출근 순)
/// 어느 쪽이든 누르면 행로표 바텀시트가 열린다.
class DutyBoardScreen extends StatefulWidget {
  const DutyBoardScreen({super.key});

  @override
  State<DutyBoardScreen> createState() => _DutyBoardScreenState();
}

enum _Mode { calendar, turns }

class _DutyBoardScreenState extends State<DutyBoardScreen> {
  late Future<DutyMonth> _future;
  late final Future<List<String>> _monthsFuture;
  _Mode _mode = _Mode.calendar;
  int? _driverNo; // null이면 나
  String? _selectedDate;

  @override
  void initState() {
    super.initState();
    _future = DutyRepository.instance.load();
    _monthsFuture = DutyRepository.instance.availableMonths();
  }

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
          if (data.drivers.isEmpty || data.dates.isEmpty) {
            return const Center(child: Text('이 달의 근무표가 비어 있습니다.'));
          }
          final me = data.driverNamed(AuthSession.current?.user.name);
          final driver = data.drivers.where((d) => d.no == _driverNo).firstOrNull ??
              me ??
              data.drivers.first;
          final today = dutyDateKey(DateTime.now());
          _selectedDate ??= data.dates.contains(today) ? today : data.dates.first;
          return Column(
            children: [
              FutureBuilder<List<String>>(
                future: _monthsFuture,
                builder: (context, months) => _Header(
                  data: data,
                  driver: driver,
                  months: months.data ?? [data.month],
                  onMonth: _loadMonth,
                  onPickDriver: () => _pickDriver(data, driver),
                  onBackToMe: me == null || me.no == driver.no
                      ? null
                      : () => setState(() => _driverNo = null),
                ),
              ),
              if (data.offline)
                const Padding(
                  padding: EdgeInsets.fromLTRB(16, 12, 16, 0),
                  child: OfflineBanner(),
                ),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                child: Row(
                  children: [
                    ActionChip(
                      label: const Text('교번'),
                      onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const RosterScreen())),
                    ),
                    const SizedBox(width: 8),
                    ActionChip(
                      label: const Text('비교'),
                      onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const CompareScreen())),
                    ),
                    const SizedBox(width: 8),
                    ActionChip(
                      label: const Text('근무 교체'),
                      onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ExchangeScreen())),
                    ),
                    const SizedBox(width: 8),
                    ActionChip(
                      label: const Text('대기충당'),
                      onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const StandbyCoverageScreen())),
                    ),
                  ],
                ),
              ),
              _ModeSwitch(mode: _mode, onChanged: (m) => setState(() => _mode = m)),
              Expanded(
                child: _mode == _Mode.calendar
                    ? _CalendarView(
                        data: data,
                        driver: driver,
                        onTapDay: (date) => _onTapDay(data, driver, date),
                      )
                    : _TurnsView(
                        data: data,
                        selectedDate: _selectedDate!,
                        onDateChanged: (d) => setState(() => _selectedDate = d),
                        onTapTurn: (a) => _showTurn(data, a.duty, '${a.driver.name} · ${_dateLabel(_selectedDate!)}'),
                      ),
              ),
            ],
          );
        },
      ),
    );
  }

  void _loadMonth(String month) => setState(() {
        _future = DutyRepository.instance.load(month);
        _selectedDate = null;
      });

  Future<void> _pickDriver(DutyMonth data, Driver current) async {
    final picked = await showModalBottomSheet<Driver>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.canvas,
      builder: (_) => _DriverPicker(drivers: data.drivers, current: current),
    );
    if (picked != null) setState(() => _driverNo = picked.no);
  }

  static String _dateLabel(String date) {
    final d = DateTime.parse(date);
    const wd = ['월', '화', '수', '목', '금', '토', '일'];
    return '${d.month}/${d.day} (${wd[d.weekday - 1]})';
  }

  /// 달력에서 하루를 눌렀을 때.
  /// 메모·교번 변경을 고칠 수 있게 근무가 없는 날도 연다.
  Future<void> _onTapDay(DutyMonth data, Driver driver, String date) async {
    await showDaySheet(context, data: data, driver: driver, date: date, subtitle: '${driver.name} · ${_dateLabel(date)}');
    if (mounted) setState(() {});
  }

  /// 그날 근무의 행로표. "70~" 아침이면 전날부터 이어지는 교번을 보여준다.
  void _showTurn(DutyMonth data, DayDuty duty, String subtitle) {
    final turn = data.turnFor(duty) ?? data.turns[duty.continues];
    if (turn == null) {
      if (duty.turn != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${duty.turn} 교번의 상세 운행 정보는 제공되지 않습니다.')),
        );
      }
      return;
    }
    showTurnSheet(
      context,
      turn: turn,
      isDummy: data.turnDetailIsDummy,
      subtitle: duty.continues != null && duty.turn == null ? '$subtitle · 전날 교번 이어서' : subtitle,
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({
    required this.data,
    required this.driver,
    required this.months,
    required this.onMonth,
    required this.onPickDriver,
    this.onBackToMe,
  });
  final DutyMonth data;
  final Driver driver;
  final List<String> months;
  final ValueChanged<String> onMonth;
  final VoidCallback onPickDriver;
  final VoidCallback? onBackToMe; // 다른 기관사를 보고 있을 때만

  @override
  Widget build(BuildContext context) {
    final ym = data.month.split('-');
    final i = months.indexOf(data.month);
    final prev = i > 0 ? months[i - 1] : null;
    final next = i >= 0 && i < months.length - 1 ? months[i + 1] : null;
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
              Row(mainAxisSize: MainAxisSize.min, children: [
                IconButton(
                  tooltip: '이전 달',
                  visualDensity: VisualDensity.compact,
                  onPressed: prev == null ? null : () => onMonth(prev),
                  icon: const Icon(Icons.chevron_left_rounded),
                ),
                Flexible(
                  child: Text('${ym[0]}년 ${int.parse(ym[1])}월',
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                ),
                IconButton(
                  tooltip: '다음 달',
                  visualDensity: VisualDensity.compact,
                  onPressed: next == null ? null : () => onMonth(next),
                  icon: const Icon(Icons.chevron_right_rounded),
                ),
              ]),
            ],
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            mainAxisSize: MainAxisSize.min,
            children: [
              OutlinedButton.icon(
                onPressed: onPickDriver,
                icon: const Icon(Icons.search_rounded, size: 18),
                label: Text('${driver.no} ${driver.name}'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppColors.ink,
                  side: BorderSide(color: AppColors.border),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(99)),
                ),
              ),
              if (onBackToMe != null)
                TextButton.icon(
                  onPressed: onBackToMe,
                  icon: const Icon(Icons.undo_rounded, size: 16),
                  label: const Text('내 스케줄로 돌아가기'),
                  style: TextButton.styleFrom(foregroundColor: AppColors.line6),
                ),
            ],
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
  const _CalendarView({required this.data, required this.driver, required this.onTapDay});
  final DutyMonth data;
  final Driver driver;
  final ValueChanged<String> onTapDay;

  @override
  Widget build(BuildContext context) {
    final first = DateTime.parse(data.dates.first);
    final leading = first.weekday % 7; // Sun=0
    const wd = ['일', '월', '화', '수', '목', '금', '토'];

    final cells = <Widget>[];
    for (var i = 0; i < leading; i++) {
      cells.add(const SizedBox.shrink());
    }
    final today = dutyDateKey(DateTime.now());
    for (final date in data.dates) {
      final duty = data.dutyOn(driver, date);
      final day = int.parse(date.split('-')[2]);
      final type = duty?.type ?? DutyType.unknown;
      final color = dutyTypeColor(type);
      cells.add(GestureDetector(
        onTap: () => onTapDay(date),
        child: Container(
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(10),
            border: date == today
                ? Border.all(color: AppColors.line6, width: 2)
                : Border.all(color: color.withValues(alpha: 0.4)),
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
                // 교번 변경 ✎ / 메모 •
                Text('${duty?.original != null ? '✎' : ''}${PersonalStore.instance.memo(driver, date) != null ? '•' : ''}',
                    style: const TextStyle(fontSize: 11, height: 1, color: AppColors.line6)),
              ],
            ),
          ),
        ),
      ));
    }

    final sum = dutySummary(data, driver);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('근무 요약', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.secondaryInk)),
        const SizedBox(height: 6),
        Wrap(
          spacing: 6,
          runSpacing: 6,
          children: [
            _Stat('총 근무', sum.work, AppColors.line6),
            _Stat('주간', sum.day, dutyTypeColor(DutyType.day)),
            _Stat('야간', sum.night, dutyTypeColor(DutyType.night)),
            _Stat('대기', sum.standby, dutyTypeColor(DutyType.standby)),
            _Stat('비번', sum.off, dutyTypeColor(DutyType.off)),
            _Stat('휴무', sum.rest, dutyTypeColor(DutyType.rest)),
          ],
        ),
        const SizedBox(height: 16),
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
        const SizedBox(height: 12),
        Text('날짜를 누르면 그날의 행로표가 열립니다.',
            style: TextStyle(fontSize: 13, color: AppColors.ghostText)),
      ],
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat(this.label, this.value, this.c);
  final String label;
  final int value;
  final Color c;

  @override
  Widget build(BuildContext context) {
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
  final ValueChanged<({Driver driver, DayDuty duty})> onTapTurn;

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
              final turn = data.turnFor(a.duty);
              final c = dutyTypeColor(a.duty.type);
              return GestureDetector(
                onTap: () => onTapTurn(a),
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
        .where((d) =>
            _q.isEmpty || d.name.contains(_q) || '${d.no}'.contains(_q) || (d.empNo?.contains(_q) ?? false))
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
                  hintText: '이름 · 연번 · 사번 검색',
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
                    subtitle: d.empNo == null ? null : Text(d.empNo!),
                    trailing: sel ? const Icon(Icons.check_rounded, color: AppColors.line6) : null,
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
