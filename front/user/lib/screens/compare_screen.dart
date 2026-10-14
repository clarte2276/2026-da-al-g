import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../core/duty_data.dart';
import '../services/auth_session.dart';
import '../widgets/projected_duty_notice.dart';

class CompareScreen extends StatefulWidget {
  const CompareScreen({super.key});

  @override
  State<CompareScreen> createState() => _CompareScreenState();
}

class _CompareScreenState extends State<CompareScreen> {
  late Future<DutyMonth> _future;
  late Future<List<String>> _monthsFuture;
  final List<Driver> _selectedDrivers = [];

  @override
  void initState() {
    super.initState();
    _future = DutyRepository.instance.load();
    _monthsFuture = DutyRepository.instance.availableMonths();
  }

  void _loadMonth(String month) {
    setState(() {
      _future = DutyRepository.instance.load(month).then((data) {
        // Update selected drivers to match the new month's driver objects
        final updated = <Driver>[];
        for (final oldDriver in _selectedDrivers) {
          final newDriver = data.driverNamed(oldDriver.name) ?? data.drivers.where((d) => d.no == oldDriver.no).firstOrNull;
          if (newDriver != null) updated.add(newDriver);
        }
        _selectedDrivers.clear();
        _selectedDrivers.addAll(updated);
        return data;
      });
    });
  }

  Future<void> _pickDriver(DutyMonth data) async {
    if (_selectedDrivers.length >= 4) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('최대 4명까지 비교할 수 있습니다.')));
      return;
    }
    final picked = await showModalBottomSheet<Driver>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.canvas,
      builder: (_) => _DriverPicker(drivers: data.drivers, selected: _selectedDrivers),
    );
    if (picked != null && !_selectedDrivers.any((d) => d.no == picked.no)) {
      setState(() => _selectedDrivers.add(picked));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(title: const Text('교번 비교', style: TextStyle(fontSize: 16))),
      body: FutureBuilder<DutyMonth>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return Center(child: Text('데이터를 불러오지 못했습니다.\n${snap.error}'));
          }
          final data = snap.data!;
          
          if (_selectedDrivers.isEmpty) {
            final me = data.driverNamed(AuthSession.current?.user.name);
            if (me != null) {
              _selectedDrivers.add(me);
            } else if (data.drivers.isNotEmpty) {
              _selectedDrivers.add(data.drivers.first);
            }
          }

          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              FutureBuilder<List<String>>(
                future: _monthsFuture,
                builder: (context, monthsSnap) {
                  final months = monthsSnap.data ?? [data.month];
                  final ym = data.month.split('-');
                  final idx = months.indexOf(data.month);
                  final prev = idx > 0 ? months[idx - 1] : null;
                  final next = idx >= 0 && idx < months.length - 1 ? months[idx + 1] : null;
                  
                  return Container(
                    color: AppColors.card,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        IconButton(
                          icon: const Icon(Icons.chevron_left),
                          onPressed: prev == null ? null : () => _loadMonth(prev),
                        ),
                        Text('${ym[0]}년 ${int.parse(ym[1])}월', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        IconButton(
                          icon: const Icon(Icons.chevron_right),
                          onPressed: next == null ? null : () => _loadMonth(next),
                        ),
                      ],
                    ),
                  );
                },
              ),
              if (data.projected)
                const Padding(
                  padding: EdgeInsets.fromLTRB(16, 8, 16, 0),
                  child: ProjectedDutyNotice(),
                ),
              
              Padding(
                padding: const EdgeInsets.all(16),
                child: Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final d in _selectedDrivers)
                      Chip(
                        label: Text(d.name),
                        onDeleted: _selectedDrivers.length > 1 ? () => setState(() => _selectedDrivers.remove(d)) : null,
                      ),
                    if (_selectedDrivers.length < 4)
                      ActionChip(
                        label: const Text('기관사 추가'),
                        avatar: const Icon(Icons.add, size: 16),
                        onPressed: () => _pickDriver(data),
                      ),
                  ],
                ),
              ),

              Expanded(
                child: SingleChildScrollView(
                  scrollDirection: Axis.vertical,
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      child: Table(
                        defaultColumnWidth: const FixedColumnWidth(60),
                        border: TableBorder.all(color: AppColors.border),
                        children: [
                          TableRow(
                            decoration: BoxDecoration(color: AppColors.softEvidence),
                            children: [
                              const TableCell(child: Padding(padding: EdgeInsets.all(8), child: Center(child: Text('일자', style: TextStyle(fontWeight: FontWeight.bold))))),
                              for (final d in _selectedDrivers)
                                TableCell(child: Padding(padding: const EdgeInsets.all(8), child: Center(child: Text(d.name, style: const TextStyle(fontWeight: FontWeight.bold))))),
                            ],
                          ),
                          for (final date in data.dates)
                            _buildRow(data, date),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  TableRow _buildRow(DutyMonth data, String date) {
    final dayStr = date.split('-')[2];
    bool allOff = true;
    final cellWidgets = <Widget>[];

    for (final driver in _selectedDrivers) {
      final duty = data.dutyOn(driver, date);
      final isOff = duty != null && !duty.type.isWork;
      if (!isOff) allOff = false;
      
      final color = duty == null ? AppColors.ink : dutyTypeColor(duty.type);
      cellWidgets.add(
        TableCell(
          child: Padding(
            padding: const EdgeInsets.all(8.0),
            child: Center(
              child: Text(
                duty?.code ?? '-',
                style: TextStyle(fontWeight: FontWeight.w800, color: color),
              ),
            ),
          ),
        ),
      );
    }

    return TableRow(
      decoration: BoxDecoration(color: allOff ? AppColors.line6Gold.withValues(alpha: 0.2) : null),
      children: [
        TableCell(
          child: Padding(
            padding: const EdgeInsets.all(8.0),
            child: Center(child: Text(dayStr)),
          ),
        ),
        ...cellWidgets,
      ],
    );
  }
}

class _DriverPicker extends StatefulWidget {
  const _DriverPicker({required this.drivers, required this.selected});
  final List<Driver> drivers;
  final List<Driver> selected;

  @override
  State<_DriverPicker> createState() => _DriverPickerState();
}

class _DriverPickerState extends State<_DriverPicker> {
  String _q = '';
  @override
  Widget build(BuildContext context) {
    final filtered = widget.drivers
        .where((d) => !widget.selected.any((s) => s.no == d.no))
        .where((d) => _q.isEmpty || d.name.contains(_q) || '${d.no}'.contains(_q) || (d.empNo?.contains(_q) ?? false))
        .toList();
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: SizedBox(
        height: MediaQuery.of(context).size.height * 0.7,
        child: Column(
          children: [
            const SizedBox(height: 12),
            const Text('비교할 기관사 추가', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
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
                  return ListTile(
                    leading: CircleAvatar(
                      backgroundColor: AppColors.softEvidence,
                      child: Text('${d.no}', style: TextStyle(fontSize: 13, color: AppColors.evidence)),
                    ),
                    title: Text(d.name),
                    subtitle: d.empNo == null ? null : Text(d.empNo!),
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
