import 'dart:async';

import 'package:flutter/material.dart';

import '../core/colors.dart';
import '../core/line6_train_map.dart';
import '../services/ai_api_client.dart';
import '../services/life_api.dart';
import '../widgets/line6_train_map.dart';
import 'life_common.dart';

/// 6호선 실시간 열차 위치. 서버 캐시 주기에 맞춰 20초마다 갱신한다.
class TrainsScreen extends StatefulWidget {
  const TrainsScreen({super.key});

  @override
  State<TrainsScreen> createState() => _TrainsScreenState();
}

class _TrainsScreenState extends State<TrainsScreen>
    with WidgetsBindingObserver {
  static const _refreshInterval = Duration(seconds: 20);
  final _api = LifeApi();
  List<Json>? _trains;
  Timer? _timer;
  String _direction = 'up';
  String? _selectedTrainNo;
  String? _error;
  bool _loading = true;
  bool _refreshing = false;
  bool _requestInFlight = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _reload();
    _timer = Timer.periodic(_refreshInterval, (_) {
      if (WidgetsBinding.instance.lifecycleState == AppLifecycleState.resumed) {
        _reload();
      }
    });
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _reload();
    }
  }

  List<Json> get _visibleTrains {
    final trains = (_trains ?? const <Json>[])
        .where((train) => train['direction'] == _direction)
        .toList();
    trains.sort((a, b) {
      final order = line6StationIndex(
        '${a['station'] ?? ''}',
      ).compareTo(line6StationIndex('${b['station'] ?? ''}'));
      return _direction == 'up' ? -order : order;
    });
    return trains;
  }

  Json? get _selectedTrain {
    for (final train in _visibleTrains) {
      if ('${train['train_no'] ?? ''}' == _selectedTrainNo) return train;
    }
    return _visibleTrains.isEmpty ? null : _visibleTrains.first;
  }

  void _selectFirstVisibleTrain() {
    final trains = _visibleTrains;
    _selectedTrainNo = trains.isEmpty
        ? null
        : '${trains.first['train_no'] ?? ''}';
  }

  Future<void> _reload() async {
    if (_requestInFlight) return;
    _requestInFlight = true;
    if (mounted) setState(() => _refreshing = true);
    try {
      final trains = await _api.fetchTrains();
      if (!mounted) return;
      setState(() {
        _trains = trains;
        _error = null;
        if (_selectedTrainNo == null ||
            !trains.any(
              (train) =>
                  train['direction'] == _direction &&
                  '${train['train_no'] ?? ''}' == _selectedTrainNo,
            )) {
          _selectFirstVisibleTrain();
        }
      });
    } on AiApiException catch (error) {
      if (mounted) {
        setState(
          () => _error = error.statusCode == 503
              ? '실시간 열차 API 키가 설정되지 않았습니다'
              : error.message,
        );
      }
    } catch (error) {
      if (mounted) setState(() => _error = '실시간 열차 정보를 불러오지 못했습니다: $error');
    } finally {
      _requestInFlight = false;
      if (mounted) {
        setState(() {
          _loading = false;
          _refreshing = false;
        });
      }
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _timer?.cancel();
    _api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => lifeScaffold(
    '6호선 실시간 열차',
    Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
          child: SegmentedButton<String>(
            showSelectedIcon: false,
            segments: const [
              ButtonSegment(value: 'up', label: Text('응암순환 방면')),
              ButtonSegment(value: 'down', label: Text('신내·봉화산 방면')),
            ],
            selected: {_direction},
            onSelectionChanged: (selection) => setState(() {
              _direction = selection.first;
              _selectFirstVisibleTrain();
            }),
          ),
        ),
        Expanded(
          child: RefreshIndicator(
            onRefresh: _reload,
            child: ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 24),
              children: [
                _summary(_visibleTrains.length),
                if (_error != null) ...[
                  const SizedBox(height: 10),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.softEvidence,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      _error!,
                      style: TextStyle(
                        color: AppColors.secondaryInk,
                        fontSize: 13,
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 10),
                if (_loading && _trains == null)
                  const SizedBox(
                    height: 300,
                    child: Center(child: CircularProgressIndicator()),
                  )
                else if (_visibleTrains.isEmpty)
                  SizedBox(
                    height: 300,
                    child: Center(
                      child: Text(
                        _error == null
                            ? '운행 중인 열차 정보가 없습니다'
                            : '열차 정보를 확인할 수 없습니다',
                        style: TextStyle(color: AppColors.secondaryInk),
                      ),
                    ),
                  )
                else ...[
                  Line6TrainMap(
                    trains: _visibleTrains,
                    direction: _direction,
                    selectedTrainNo: '${_selectedTrain?['train_no'] ?? ''}',
                    onSelectTrain: (train) => setState(
                      () => _selectedTrainNo = '${train['train_no'] ?? ''}',
                    ),
                  ),
                  if (_selectedTrain != null) _trainDetails(_selectedTrain!),
                ],
                const SizedBox(height: 16),
                Text(
                  '출처: 서울특별시 공공데이터',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: AppColors.ghostText, fontSize: 10),
                ),
              ],
            ),
          ),
        ),
      ],
    ),
    actions: [
      IconButton(
        tooltip: '새로고침',
        onPressed: _refreshing ? null : _reload,
        icon: _refreshing
            ? SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: AppColors.line6,
                ),
              )
            : const Icon(Icons.refresh_rounded),
      ),
    ],
  );

  Widget _summary(int count) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
    decoration: BoxDecoration(
      color: AppColors.card,
      border: Border.all(color: AppColors.border),
      borderRadius: BorderRadius.circular(14),
    ),
    child: Row(
      children: [
        const Icon(Icons.train_rounded, color: AppColors.line6),
        const SizedBox(width: 9),
        Expanded(
          child: Text(
            _loading && _trains == null
                ? '열차 정보를 확인하고 있습니다'
                : '현재 운행 열차 $count대',
            style: TextStyle(color: AppColors.ink, fontWeight: FontWeight.w700),
          ),
        ),
        Text(
          '20초마다 갱신',
          style: TextStyle(color: AppColors.ghostText, fontSize: 11),
        ),
      ],
    ),
  );

  Widget _trainDetails(Json train) {
    final crewName = '${train['crew_name'] ?? '신내사업소'}';
    final crewTurn = '${train['crew_turn'] ?? ''}';
    final terminal = '${train['terminal'] ?? ''}';
    return Container(
      margin: const EdgeInsets.only(top: 6),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.card,
        border: Border.all(color: AppColors.border),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${train['train_no'] ?? ''}열차 · ${train['station'] ?? ''} ${train['status'] ?? ''}',
            style: TextStyle(color: AppColors.ink, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 4),
          Text(
            '$terminal행 · ${shortTime(train['updated_at'])}',
            style: TextStyle(color: AppColors.secondaryInk, fontSize: 12),
          ),
          const SizedBox(height: 8),
          Text(
            '승무원  $crewName${crewTurn.isEmpty ? '' : ' · $crewTurn'}',
            style: TextStyle(
              color: AppColors.line6GoldDeep,
              fontSize: 13,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}
