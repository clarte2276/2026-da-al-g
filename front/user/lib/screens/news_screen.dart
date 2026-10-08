import 'package:flutter/material.dart';
import '../services/life_api.dart';
import 'life_common.dart';

class NewsScreen extends StatefulWidget {
  const NewsScreen({super.key});
  @override
  State<NewsScreen> createState() => _NewsScreenState();
}

class _NewsScreenState extends State<NewsScreen> {
  final _api = LifeApi();
  late Future<List<Json>> _future = _api.fetchNews();

  Future<void> _reload() async {
    setState(() => _future = _api.fetchNews());
    await _future.catchError((_) => <Json>[]);
  }

  @override
  void dispose() {
    _api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => lifeScaffold(
        '헤드라인 뉴스',
        AsyncList(
          future: _future,
          onRefresh: _reload,
          empty: '뉴스를 가져오지 못했습니다 (약 10분마다 갱신)',
          item: (n) => InfoCard(
            title: n['title'] ?? '',
            subtitle: '${n['source'] ?? ''} · ${shortTime(n['published'])}',
            onTap: () => openLink(context, '${n['link']}'),
          ),
        ),
      );
}
