import 'package:flutter/material.dart';
import '../core/colors.dart';

class _Block {
  final int startMin;
  final int durationMin;
  final String label;
  final String timeRange;
  final Color color;

  const _Block({
    required this.startMin,
    required this.durationMin,
    required this.label,
    required this.timeRange,
    required this.color,
  });
}

const _mockBlocks = {
  '화': [
    _Block(startMin: 90,  durationMin: 550, label: '오전 교번', timeRange: '06:30–15:40', color: Color(0xff2e5b9a)),
  ],
  '수': [
    _Block(startMin: 560, durationMin: 490, label: '오후 교번', timeRange: '14:20–22:30', color: AppColors.line6Gold),
  ],
  '목': [
    _Block(startMin: 315, durationMin: 550, label: '오전 교번', timeRange: '10:15–19:25', color: Color(0xff2e5b9a)),
  ],
  '금': [
    _Block(startMin: 720, durationMin: 390, label: '야간 교번', timeRange: '17:00–23:30', color: Color(0xff5a4e9a)),
  ],
  '일': [
    _Block(startMin: 225, durationMin: 550, label: '오전 교번', timeRange: '08:45–17:55', color: Color(0xff2e5b9a)),
  ],
};

class WeeklyGridView extends StatelessWidget {
  const WeeklyGridView({super.key});

  static const _startHour = 5;
  static const _endHour = 24;
  static const _hourH = 36.0;
  static const _timeColW = 34.0;
  static const _totalGridH = (_endHour - _startHour) * _hourH; // 684
  static const _days = ['월', '화', '수', '목', '금', '토', '일'];
  static const _todayIndex = 2; // 수

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.border),
      ),
      clipBehavior: Clip.hardEdge,
      child: Column(
        children: [
          _DayHeader(days: _days, todayIndex: _todayIndex),
          Divider(height: 1, color: AppColors.border),
          SizedBox(
            height: _totalGridH,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _TimeColumn(startHour: _startHour, endHour: _endHour, hourH: _hourH, width: _timeColW),
                Expanded(
                  child: _GridArea(
                    days: _days,
                    todayIndex: _todayIndex,
                    startHour: _startHour,
                    endHour: _endHour,
                    hourH: _hourH,
                    blocks: _mockBlocks,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _DayHeader extends StatelessWidget {
  const _DayHeader({required this.days, required this.todayIndex});
  final List<String> days;
  final int todayIndex;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        SizedBox(width: WeeklyGridView._timeColW),
        ...List.generate(days.length, (i) {
          final isToday = i == todayIndex;
          return Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 8),
              color: isToday ? AppColors.line6Gold.withValues(alpha: 0.08) : null,
              child: Column(
                children: [
                  Text(
                    days[i],
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: isToday ? FontWeight.w800 : FontWeight.w500,
                      color: isToday ? AppColors.line6Gold : AppColors.secondaryInk,
                    ),
                  ),
                  if (isToday) ...[
                    const SizedBox(height: 3),
                    Container(
                      width: 5,
                      height: 5,
                      decoration: const BoxDecoration(color: AppColors.line6Gold, shape: BoxShape.circle),
                    ),
                  ],
                ],
              ),
            ),
          );
        }),
      ],
    );
  }
}

class _TimeColumn extends StatelessWidget {
  const _TimeColumn({
    required this.startHour,
    required this.endHour,
    required this.hourH,
    required this.width,
  });
  final int startHour, endHour;
  final double hourH, width;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: width,
      child: Stack(
        children: List.generate(endHour - startHour, (i) {
          final hour = startHour + i;
          return Positioned(
            top: i * hourH - 6,
            left: 0,
            right: 0,
            child: Text(
              hour.toString().padLeft(2, '0'),
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 9, color: AppColors.ghostText, height: 1),
            ),
          );
        }),
      ),
    );
  }
}

class _GridArea extends StatelessWidget {
  const _GridArea({
    required this.days,
    required this.todayIndex,
    required this.startHour,
    required this.endHour,
    required this.hourH,
    required this.blocks,
  });
  final List<String> days;
  final int todayIndex, startHour, endHour;
  final double hourH;
  final Map<String, List<_Block>> blocks;

  @override
  Widget build(BuildContext context) {
    final totalH = (endHour - startHour) * hourH;
    final hours = endHour - startHour;

    return LayoutBuilder(
      builder: (ctx, constraints) {
        final colW = constraints.maxWidth / days.length;

        // Build duty block positioned widgets
        final blockWidgets = <Widget>[];
        for (var di = 0; di < days.length; di++) {
          for (final b in blocks[days[di]] ?? []) {
            final top = b.startMin / 60 * hourH;
            final height = (b.durationMin / 60 * hourH).clamp(20.0, double.infinity);
            blockWidgets.add(Positioned(
              left: di * colW + 2,
              width: colW - 4,
              top: top,
              height: height,
              child: _BlockTile(block: b, height: height),
            ));
          }
        }

        return Stack(
          children: [
            // Hour lines
            ...List.generate(hours, (i) => Positioned(
              top: i * hourH,
              left: 0,
              right: 0,
              child: Divider(
                height: 1,
                color: i == 0 ? Colors.transparent : AppColors.border.withValues(alpha: 0.5),
              ),
            )),

            // Today column tint
            Positioned(
              left: todayIndex * colW,
              width: colW,
              top: 0,
              height: totalH,
              child: Container(color: AppColors.line6Gold.withValues(alpha: 0.04)),
            ),

            // Vertical day dividers
            ...List.generate(days.length - 1, (i) => Positioned(
              left: (i + 1) * colW,
              top: 0,
              bottom: 0,
              width: 1,
              child: Container(color: AppColors.border.withValues(alpha: 0.5)),
            )),

            // Duty blocks
            ...blockWidgets,
          ],
        );
      },
    );
  }
}

class _BlockTile extends StatelessWidget {
  const _BlockTile({required this.block, required this.height});
  final _Block block;
  final double height;

  @override
  Widget build(BuildContext context) {
    final isTall = height > 56;
    return Container(
      decoration: BoxDecoration(
        color: block.color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(6),
        border: Border(left: BorderSide(color: block.color, width: 3)),
      ),
      padding: const EdgeInsets.fromLTRB(5, 4, 4, 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            block.label,
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              color: block.color,
              height: 1.1,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          if (isTall) ...[
            const SizedBox(height: 2),
            Text(
              block.timeRange,
              style: TextStyle(fontSize: 9, color: block.color.withValues(alpha: 0.8), height: 1.2),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ],
      ),
    );
  }
}
