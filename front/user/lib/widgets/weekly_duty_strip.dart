import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../core/duty_data.dart';

/// dia5의 "주간 일정" 가로 스트립을 차용한 위젯.
/// 이번 주 7일을 요일·날짜·근무유형(주간/야간/비번/휴무) 칩으로 보여준다.
class WeeklyDutyStrip extends StatelessWidget {
  const WeeklyDutyStrip({super.key, this.onTapDay});
  final VoidCallback? onTapDay;

  static const _labels = ['주간', '야간', '비번', '휴무', '주간', '대기', '휴무'];

  DutyType _typeOf(String label) {
    switch (label) {
      case '주간':
        return DutyType.day;
      case '야간':
        return DutyType.night;
      case '대기':
        return DutyType.standby;
      case '비번':
        return DutyType.off;
      case '휴무':
        return DutyType.rest;
      default:
        return DutyType.unknown;
    }
  }

  @override
  Widget build(BuildContext context) {
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
          final label = _labels[i];
          final c = dutyTypeColor(_typeOf(label));
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
                        fontSize: 12,
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
                    child: Text(label,
                        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: c)),
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
