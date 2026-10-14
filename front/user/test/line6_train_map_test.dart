import 'package:flutter_test/flutter_test.dart';
import 'package:user/core/line6_train_map.dart';

void main() {
  final geometry = createLine6MapGeometry();

  test('includes all 39 stations and normalizes the ShinNae alias', () {
    expect(geometry.stations, hasLength(39));
    expect(line6StationIndex('신내역'), 38);
    expect(
      line6StationIndex('월드컵경기장 (마포구청)'),
      line6StationNames.indexOf('월드컵경기장'),
    );
    expect(line6StationIndex('강남'), -1);
  });

  test('places an arrived train on its station for either direction', () {
    final station = geometry.mainStations.firstWhere(
      (item) => item.name == '마포구청',
    );
    for (final direction in ['up', 'down']) {
      final point = line6TrainMapPoint(
        geometry,
        stationName: '마포구청',
        direction: direction,
        status: '도착',
      );
      expect(point?.x, station.x);
      expect(point?.y, station.y);
    }
  });

  test('preserves the folded outer track between Mangwon and Hapjeong', () {
    final mangwon = geometry.mainStations.firstWhere(
      (item) => item.name == '망원',
    );
    final hapjeong = geometry.mainStations.firstWhere(
      (item) => item.name == '합정',
    );
    final point = line6TrainMapPoint(
      geometry,
      stationName: '망원',
      direction: 'down',
      status: '출발',
    );
    expect(mangwon.x, hapjeong.x);
    expect(point?.x, mangwon.x);
  });

  test('moves a departed Eungam-bound train toward the previous station', () {
    final station = geometry.mainStations.firstWhere(
      (item) => item.name == '마포구청',
    );
    final point = line6TrainMapPoint(
      geometry,
      stationName: '마포구청',
      direction: 'up',
      status: '출발',
    );
    expect(point, isNotNull);
    expect(point!.x, lessThan(station.x));
  });

  test('positions loop stations and ignores stations outside Line 6', () {
    final dokbawi = geometry.loopStations.firstWhere(
      (item) => item.name == '독바위',
    );
    final point = line6TrainMapPoint(
      geometry,
      stationName: '독바위',
      direction: 'down',
      status: '도착',
    );
    expect(point?.x, dokbawi.x);
    expect(point?.y, dokbawi.y);
    expect(
      line6TrainMapPoint(
        geometry,
        stationName: '강남',
        direction: 'up',
        status: '도착',
      ),
      isNull,
    );
  });
}
