import 'package:flutter/material.dart';

import '../core/colors.dart';
import '../core/line6_train_map.dart';

class Line6TrainMap extends StatelessWidget {
  const Line6TrainMap({
    super.key,
    required this.trains,
    required this.direction,
    required this.selectedTrainNo,
    required this.onSelectTrain,
  });

  final List<Map<String, dynamic>> trains;
  final String direction;
  final String? selectedTrainNo;
  final ValueChanged<Map<String, dynamic>> onSelectTrain;

  @override
  Widget build(BuildContext context) => SizedBox(
    height: 410,
    child: LayoutBuilder(
      builder: (context, constraints) {
        final geometry = createLine6MapGeometry(width: constraints.maxWidth);
        return Stack(
          clipBehavior: Clip.none,
          children: [
            Positioned.fill(
              child: Semantics(
                label: '6호선 노선도. 역 순서: ${line6StationNames.join(', ')}',
                child: CustomPaint(painter: _Line6MapPainter(geometry)),
              ),
            ),
            for (final train in trains)
              if (_pointFor(train, geometry) case final point?)
                Positioned(
                  left: (point.x - 39).clamp(0, geometry.width - 78).toDouble(),
                  top: (point.y + (direction == 'up' ? -39 : 7))
                      .clamp(0, geometry.height - 39)
                      .toDouble(),
                  child: _TrainMarker(
                    train: train,
                    color: direction == 'up'
                        ? AppColors.line6
                        : const Color(0xff3c78af),
                    selected: '${train['train_no'] ?? ''}' == selectedTrainNo,
                    onTap: () => onSelectTrain(train),
                  ),
                ),
          ],
        );
      },
    ),
  );

  Line6MapPoint? _pointFor(
    Map<String, dynamic> train,
    Line6MapGeometry geometry,
  ) => line6TrainMapPoint(
    geometry,
    stationName: '${train['station'] ?? ''}',
    direction: direction,
    status: '${train['status'] ?? ''}',
  );
}

class _TrainMarker extends StatelessWidget {
  const _TrainMarker({
    required this.train,
    required this.color,
    required this.selected,
    required this.onTap,
  });

  final Map<String, dynamic> train;
  final Color color;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final status = '${train['status'] ?? ''}';
    final crewTurn = '${train['crew_turn'] ?? ''}';
    final statusColor = status.contains('도착')
        ? const Color(0xff398b61)
        : status.contains('출발')
        ? const Color(0xffc47e2c)
        : AppColors.evidence;
    return Material(
      elevation: selected ? 4 : 1,
      color: AppColors.card,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(9),
        side: BorderSide(
          color: selected ? AppColors.ink : color,
          width: selected ? 2 : 1.2,
        ),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(9),
        onTap: onTap,
        child: SizedBox(
          width: 78,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 3),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 6,
                      height: 6,
                      decoration: BoxDecoration(
                        color: statusColor,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 3),
                    Flexible(
                      child: Text(
                        '${train['train_no'] ?? ''}열차',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                          color: AppColors.ink,
                        ),
                      ),
                    ),
                  ],
                ),
                Text(
                  '${train['crew_name'] ?? '신내사업소'}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 8,
                    fontWeight: FontWeight.w600,
                    color: AppColors.secondaryInk,
                  ),
                ),
                if (crewTurn.isNotEmpty)
                  Text(
                    crewTurn,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontSize: 7, color: AppColors.ghostText),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _Line6MapPainter extends CustomPainter {
  const _Line6MapPainter(this.geometry);

  final Line6MapGeometry geometry;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.scale(size.width / geometry.width, size.height / geometry.height);

    final trackPaint = Paint()
      ..color = AppColors.line6
      ..strokeWidth = 4
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round
      ..style = PaintingStyle.stroke;
    _drawPath(canvas, geometry.mainTrackPath, trackPaint);
    _drawPath(canvas, geometry.loopTrackPath, trackPaint);

    for (final station in geometry.stations) {
      canvas.drawCircle(
        Offset(station.x, station.y),
        4,
        Paint()..color = AppColors.card,
      );
      canvas.drawCircle(
        Offset(station.x, station.y),
        4,
        Paint()
          ..color = AppColors.line6
          ..strokeWidth = 2
          ..style = PaintingStyle.stroke,
      );
      final name = switch (station.name) {
        '디지털미디어시티' => 'DMC',
        '월드컵경기장' => '월드컵',
        '효창공원앞' => '효창공원',
        _ => station.name,
      };
      final label = TextPainter(
        text: TextSpan(
          text: name,
          style: TextStyle(
            color: AppColors.ink,
            fontSize: 8,
            fontWeight: FontWeight.w700,
          ),
        ),
        textDirection: TextDirection.ltr,
        maxLines: 1,
        ellipsis: '…',
      )..layout(maxWidth: 45);
      final offset = switch (station.labelPosition) {
        'top' => Offset(
          station.x - label.width / 2,
          station.y - label.height - 7,
        ),
        'left' => Offset(
          station.x - label.width - 7,
          station.y - label.height / 2,
        ),
        'right' => Offset(station.x + 7, station.y - label.height / 2),
        _ => Offset(station.x - label.width / 2, station.y + 7),
      };
      label.paint(canvas, offset);
    }
    canvas.restore();
  }

  void _drawPath(Canvas canvas, List<Line6MapPoint> points, Paint paint) {
    final path = Path()..moveTo(points.first.x, points.first.y);
    for (final point in points.skip(1)) {
      path.lineTo(point.x, point.y);
    }
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant _Line6MapPainter oldDelegate) =>
      oldDelegate.geometry.width != geometry.width ||
      oldDelegate.geometry.height != geometry.height;
}
