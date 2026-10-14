import 'dart:math' as math;

const line6StationNames = <String>[
  '응암',
  '역촌',
  '불광',
  '독바위',
  '연신내',
  '구산',
  '새절',
  '증산',
  '디지털미디어시티',
  '월드컵경기장',
  '마포구청',
  '망원',
  '합정',
  '상수',
  '광흥창',
  '대흥',
  '공덕',
  '효창공원앞',
  '삼각지',
  '녹사평',
  '이태원',
  '한강진',
  '버티고개',
  '약수',
  '청구',
  '신당',
  '동묘앞',
  '창신',
  '보문',
  '안암',
  '고려대',
  '월곡',
  '상월곡',
  '돌곶이',
  '석계',
  '태릉입구',
  '화랑대',
  '봉화산',
  '신내',
];

const _mainStationNames = <String>[
  '응암',
  '새절',
  '증산',
  '디지털미디어시티',
  '월드컵경기장',
  '마포구청',
  '망원',
  '합정',
  '상수',
  '광흥창',
  '대흥',
  '공덕',
  '효창공원앞',
  '삼각지',
  '녹사평',
  '이태원',
  '한강진',
  '버티고개',
  '약수',
  '청구',
  '신당',
  '동묘앞',
  '창신',
  '보문',
  '안암',
  '고려대',
  '월곡',
  '상월곡',
  '돌곶이',
  '석계',
  '태릉입구',
  '화랑대',
  '봉화산',
  '신내',
];

class Line6MapPoint {
  const Line6MapPoint(this.x, this.y);

  final double x;
  final double y;
}

class Line6MapStation extends Line6MapPoint {
  const Line6MapStation(super.x, super.y, this.name, this.labelPosition);

  final String name;
  final String labelPosition;
}

class Line6MapGeometry {
  const Line6MapGeometry({
    required this.width,
    required this.height,
    required this.mainTrackPath,
    required this.loopTrackPath,
    required this.mainStations,
    required this.loopStations,
    required this.stations,
  });

  final double width;
  final double height;
  final List<Line6MapPoint> mainTrackPath;
  final List<Line6MapPoint> loopTrackPath;
  final List<Line6MapStation> mainStations;
  final List<Line6MapStation> loopStations;
  final List<Line6MapStation> stations;
}

int line6StationIndex(String stationName) {
  var name = stationName.replaceAll(RegExp(r'\s*\([^)]*\)\s*$'), '').trim();
  if (name == '신내역') name = '신내';
  return line6StationNames.indexOf(name);
}

Line6MapGeometry createLine6MapGeometry({
  double width = 340,
  double height = 410,
}) {
  final safeWidth = math.max(300, width).toDouble();
  final safeHeight = math.max(360, height).toDouble();
  const inset = 22.0;
  const corner = 14.0;
  final top = safeHeight * 0.27;
  final bottom = safeHeight * 0.9;
  final rowGap = (bottom - top) / 3;
  final second = top + rowGap;
  final third = second + rowGap;
  final left = inset;
  final right = safeWidth - inset;
  final straightLeft = left + corner;
  final straightRight = right - corner;
  final firstX = straightRight - (straightRight - straightLeft) / 6 * 5;

  List<Line6MapPoint> horizontal(
    int count,
    double fromX,
    double toX,
    double y,
  ) => List.generate(
    count,
    (i) => Line6MapPoint(
      fromX + (toX - fromX) * (count == 1 ? 0 : i / (count - 1)),
      y,
    ),
  );
  List<Line6MapPoint> vertical(double x, double fromY, double toY) => [
    Line6MapPoint(x, fromY + (toY - fromY) / 3),
    Line6MapPoint(x, fromY + (toY - fromY) * 2 / 3),
  ];

  final mainTrackPath = <Line6MapPoint>[
    Line6MapPoint(firstX, top),
    Line6MapPoint(right, top),
    Line6MapPoint(right, second),
    Line6MapPoint(left, second),
    Line6MapPoint(left, third),
    Line6MapPoint(right, third),
    Line6MapPoint(right, bottom),
    Line6MapPoint(left, bottom),
  ];
  final positions = <Line6MapPoint>[
    ...horizontal(6, firstX, straightRight, top),
    ...vertical(right, top, second),
    ...horizontal(7, straightRight, straightLeft, second),
    ...vertical(left, second, third),
    ...horizontal(7, straightLeft, straightRight, third),
    ...vertical(right, third, bottom),
    ...horizontal(8, straightRight, left, bottom),
  ];
  final mainStations = List.generate(
    _mainStationNames.length,
    (i) => Line6MapStation(
      positions[i].x,
      positions[i].y,
      _mainStationNames[i],
      i.isEven ? 'bottom' : 'top',
    ),
  );
  final loopTop = 42 * safeHeight / 410;
  final loopBottom = 126 * safeHeight / 410;
  final eungam = mainStations.first;
  final loopStations = <Line6MapStation>[
    eungam,
    Line6MapStation(eungam.x, 70 * safeHeight / 410, '역촌', 'right'),
    Line6MapStation(58, loopTop, '불광', 'top'),
    Line6MapStation(18, 64 * safeHeight / 410, '독바위', 'right'),
    Line6MapStation(18, 105 * safeHeight / 410, '연신내', 'right'),
    Line6MapStation(55, loopBottom, '구산', 'bottom'),
  ];
  return Line6MapGeometry(
    width: safeWidth,
    height: safeHeight,
    mainTrackPath: mainTrackPath,
    loopTrackPath: [
      eungam,
      Line6MapPoint(eungam.x, 70 * safeHeight / 410),
      Line6MapPoint(eungam.x, loopTop),
      Line6MapPoint(58, loopTop),
      Line6MapPoint(18, loopTop),
      Line6MapPoint(18, 64 * safeHeight / 410),
      Line6MapPoint(18, 105 * safeHeight / 410),
      Line6MapPoint(18, loopBottom),
      Line6MapPoint(55, loopBottom),
      Line6MapPoint(eungam.x, loopBottom),
      Line6MapPoint(eungam.x, eungam.y),
      eungam,
    ],
    mainStations: mainStations,
    loopStations: loopStations,
    stations: [...mainStations, ...loopStations.skip(1)],
  );
}

Line6MapPoint? line6TrainMapPoint(
  Line6MapGeometry geometry, {
  required String stationName,
  required String direction,
  required String status,
}) {
  final index = line6StationIndex(stationName);
  if (index < 0) return null;
  final current = geometry.stations.firstWhere(
    (station) => station.name == line6StationNames[index],
  );
  if (status.contains('도착')) return current;

  final step = direction == 'up' ? -1 : 1;
  final bool departing = status == '출발';
  final fromIndex = departing ? index : index - step;
  final toIndex = departing ? index + step : index;
  if (fromIndex < 0 ||
      toIndex < 0 ||
      fromIndex >= line6StationNames.length ||
      toIndex >= line6StationNames.length) {
    return current;
  }
  final from = geometry.stations.firstWhere(
    (station) => station.name == line6StationNames[fromIndex],
  );
  final to = geometry.stations.firstWhere(
    (station) => station.name == line6StationNames[toIndex],
  );
  final progress = departing
      ? 0.12
      : status.contains('진입')
      ? 0.82
      : status.contains('전역출발')
      ? 0.12
      : 0.5;
  return Line6MapPoint(
    from.x + (to.x - from.x) * progress,
    from.y + (to.y - from.y) * progress,
  );
}
