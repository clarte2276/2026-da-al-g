import 'package:flutter/material.dart';
import '../core/colors.dart';
import 'app_card.dart';

class TrainFlowTimeline extends StatelessWidget {
  const TrainFlowTimeline({super.key});

  @override
  Widget build(BuildContext context) {
    const items = [
      ('14:20', '출무 보고'),
      ('14:47', '응암 출발'),
      ('15:58', '신내 도착'),
      ('18:10', '휴게'),
      ('22:30', '근무 종료'),
    ];
    return AppCard(
      child: Column(
        children: List.generate(
          items.length,
          (i) => _TimelineRow(time: items[i].$1, label: items[i].$2, isLast: i == items.length - 1),
        ),
      ),
    );
  }
}

class _TimelineRow extends StatelessWidget {
  const _TimelineRow({required this.time, required this.label, required this.isLast});
  final String time, label;
  final bool isLast;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 50,
      child: Row(
        children: [
          SizedBox(
            width: 50,
            child: Text(time, style: TextStyle(color: AppColors.secondaryInk, fontWeight: FontWeight.w600)),
          ),
          Column(
            children: [
              Container(
                width: 10,
                height: 10,
                decoration: const BoxDecoration(color: AppColors.line6Gold, shape: BoxShape.circle),
              ),
              if (!isLast) Expanded(child: Container(width: 2, color: AppColors.border)),
            ],
          ),
          const SizedBox(width: 16),
          Text(label, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}
