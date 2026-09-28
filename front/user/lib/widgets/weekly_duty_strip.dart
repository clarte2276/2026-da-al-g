import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../core/duty_data.dart';
import '../services/auth_session.dart';

/// 이번 주 7일의 내 근무 유형을 근무표 JSON에서 읽어 보여준다. 없는 날은 '-'.
class WeeklyDutyStrip extends StatelessWidget {
  const WeeklyDutyStrip({super.key, this.onTapDay});
  final VoidCallback? onTapDay;

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<DutyMonth>(
      future: DutyRepository.instance.load(),
      builder: (context, snap) =>
          _strip(snap.data?.driverNamed(AuthSession.current?.user.name)),
    );
  }

  Widget _strip(Driver? me) {
    final now = DateTime.now();
    final sunday = now.subtract(Duration(days: now.weekday % 7));
    const wd = ['일', '월', '화', '수', '목', '금', '토'];

    return SizedBox(
      height: 108,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(vertical: 2),
        itemCount: 7,
        separatorBuilder: (_, _) => const SizedBox(width: 8),
        itemBuilder: (context, i) {
          final date = sunday.add(Duration(days: i));
          final isToday = date.year == now.year &&
              date.month == now.month &&
              date.day == now.day;
          final type = me?.days[dutyDateKey(date)]?.type ?? DutyType.unknown;
          final c = dutyTypeColor(type);
          return GestureDetector(
            onTap: onTapDay,
            child: Container(
              width: 60,
              decoration: BoxDecoration(
                color: AppColors.card,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                  color: isToday ? AppColors.line6Gold : AppColors.border,
                  width: isToday ? 2 : 1,
                ),
              ),
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(wd[i],
                      style: TextStyle(
                        fontSize: 13,
                        color: i == 0
                            ? Colors.red.shade400
                            : (i == 6 ? Colors.blue.shade400 : AppColors.secondaryInk),
                      )),
                  const SizedBox(height: 2),
                  Text('${date.day}',
                      style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: c.withValues(alpha: 0.14),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(type.label,
                        style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: c)),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
