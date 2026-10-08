import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../core/duty_data.dart';
import '../widgets/app_card.dart';
import '../widgets/page_header.dart';

class RosterScreen extends StatefulWidget {
  const RosterScreen({super.key});

  @override
  State<RosterScreen> createState() => _RosterScreenState();
}

class _RosterScreenState extends State<RosterScreen> {
  late Future<DutyMonth> _future;
  String? _selectedDate;

  @override
  void initState() {
    super.initState();
    _future = DutyRepository.instance.load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(title: const Text('교번', style: TextStyle(fontSize: 16))),
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
          if (data.dates.isEmpty) return const Center(child: Text('데이터가 없습니다.'));
          
          final today = dutyDateKey(DateTime.now());
          _selectedDate ??= data.dates.contains(today) ? today : data.dates.first;

          final grouped = <DutyType, List<({Driver driver, DayDuty duty})>>{};
          for (final type in DutyType.values) {
            grouped[type] = [];
          }

          for (final driver in data.drivers) {
            final duty = data.dutyOn(driver, _selectedDate!);
            if (duty != null) {
              grouped[duty.type]!.add((driver: driver, duty: duty));
            }
          }

          // Sort day/night/standby by depart time if available
          int sortKey(DayDuty duty) {
            final turn = data.turnFor(duty);
            final timeStr = turn?.depart ?? '';
            final m = RegExp(r'^(\d{1,2}):(\d{2})$').firstMatch(timeStr.trim());
            if (m == null) return 9999;
            return int.parse(m[1]!) * 60 + int.parse(m[2]!);
          }
          
          for (final list in grouped.values) {
            list.sort((a, b) => sortKey(a.duty).compareTo(sortKey(b.duty)));
          }

          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                child: const PageHeader(title: '일일 교번'),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: AppCard(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  child: Row(
                    children: [
                      const Icon(Icons.calendar_today_rounded, size: 20),
                      const SizedBox(width: 12),
                      Expanded(
                        child: DropdownButtonHideUnderline(
                          child: DropdownButton<String>(
                            value: _selectedDate,
                            isExpanded: true,
                            items: data.dates.map((date) {
                              return DropdownMenuItem(value: date, child: Text(date));
                            }).toList(),
                            onChanged: (v) {
                              if (v != null) setState(() => _selectedDate = v);
                            },
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              Expanded(
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _buildSection('주간', grouped[DutyType.day]!, data),
                    _buildSection('야간', grouped[DutyType.night]!, data),
                    _buildSection('대기', grouped[DutyType.standby]!, data),
                    _buildSection('비번', grouped[DutyType.off]!, data),
                    _buildSection('휴무', grouped[DutyType.rest]!, data),
                    _buildSection('지정', grouped[DutyType.designated]!, data),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildSection(String title, List<({Driver driver, DayDuty duty})> items, DutyMonth data) {
    if (items.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(top: 16, bottom: 8, left: 4),
          child: Text(
            '$title (${items.length})',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppColors.ink),
          ),
        ),
        AppCard(
          padding: EdgeInsets.zero,
          child: ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: items.length,
            separatorBuilder: (_, _) => Divider(height: 1, color: AppColors.border),
            itemBuilder: (context, i) {
              final item = items[i];
              final turn = data.turnFor(item.duty);
              final hasTimes = turn != null && turn.depart.isNotEmpty && turn.arrive.isNotEmpty;
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                child: Row(
                  children: [
                    SizedBox(
                      width: 40,
                      child: Text(
                        item.duty.code,
                        style: TextStyle(fontWeight: FontWeight.w800, color: dutyTypeColor(item.duty.type)),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        item.driver.name,
                        style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                      ),
                    ),
                    if (hasTimes)
                      Text(
                        '${turn.depart} ~ ${turn.arrive}',
                        style: TextStyle(fontSize: 13, color: AppColors.secondaryInk),
                      ),
                  ],
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}
