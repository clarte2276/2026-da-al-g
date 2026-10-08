import 'dart:async';
import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../services/life_api.dart';
import 'life_common.dart';

/// 6호선 실시간 열차 위치. 화면이 열려 있는 동안 30초마다 갱신한다.
class TrainsScreen extends StatefulWidget {
  const TrainsScreen({super.key});
  @override
  State<TrainsScreen> createState() => _TrainsScreenState();
}

class _TrainsScreenState extends State<TrainsScreen> {
  final _api = LifeApi();
  late Future<List<Json>> _all = _api.fetchTrains();
  late Future<List<Json>> _shown = _filter();
  Timer? _timer;
  String _direction = 'up';

  Future<List<Json>> _filter() => _all.then((all) => all.where((t) => t['direction'] == _direction).toList());

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 30), (_) => _reload());
  }

  Future<void> _reload() async {
    if (!mounted) return;
    setState(() {
      _all = _api.fetchTrains();
      _shown = _filter();
    });
    await _shown.catchError((_) => <Json>[]);
  }

  @override
  void dispose() {
    _timer?.cancel();
    _api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => lifeScaffold(
        '6호선 실시간',
        Column(children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: SegmentedButton<String>(
              segments: const [ButtonSegment(value: 'up', label: Text('상행')), ButtonSegment(value: 'down', label: Text('하행'))],
              selected: {_direction},
              onSelectionChanged: (s) => setState(() {
                _direction = s.first;
                _shown = _filter();
              }),
            ),
          ),
          Expanded(
            child: AsyncList(
              future: _shown,
              onRefresh: _reload,
              empty: '운행 중인 열차 정보가 없습니다',
              item: (t) => InfoCard(
                leading: Icon(Icons.train, color: AppColors.line6),
                title: '${t['station']}  ${t['status']}',
                subtitle: '${t['train_no']}열차 · ${t['terminal']}행 · ${t['updated_at']}',
              ),
            ),
          ),
        ]),
      );
}
