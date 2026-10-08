import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../services/life_api.dart';
import 'life_common.dart';

const _severity = {'info': ('안내', Colors.blueGrey), 'warning': ('주의', Colors.orange), 'danger': ('위험', Colors.red)};
const _categories = {'hazard': '위험개소', 'action': '조치요청', 'inspect': '점검'};
const _statuses = {'open': '접수', 'in_progress': '처리중', 'resolved': '완료'};

class SafetyScreen extends StatelessWidget {
  const SafetyScreen({super.key});

  @override
  Widget build(BuildContext context) => DefaultTabController(
        length: 3,
        child: lifeScaffold(
          '안전관리',
          const TabBarView(children: [_AlertsTab(), _HazardsTab(), _TipsTab()]),
          bottom: const TabBar(tabs: [Tab(text: '알림'), Tab(text: '신고'), Tab(text: '안전상식')]),
        ),
      );
}

class _AlertsTab extends StatefulWidget {
  const _AlertsTab();
  @override
  State<_AlertsTab> createState() => _AlertsTabState();
}

class _AlertsTabState extends State<_AlertsTab> {
  final _api = LifeApi();
  late Future<List<Json>> _future = _api.fetchAlerts();

  Future<void> _reload() async {
    setState(() => _future = _api.fetchAlerts());
    await _future.catchError((_) => <Json>[]);
  }

  Future<void> _create() async {
    final v = await promptFields(context, '안전 알림 등록', ['출발역', '도착역', '내용 (위험 표시는 맨 앞에 !)'], maxLines: 4);
    if (v == null || !mounted || v[2].isEmpty) return;
    final danger = v[2].startsWith('!');
    final ok = await runAction(context, () => _api.createAlert({
          'station_from': v[0],
          'station_to': v[1],
          'message': danger ? v[2].substring(1).trim() : v[2],
          'severity': danger ? 'danger' : 'warning',
        }));
    if (ok) _reload();
  }

  @override
  void dispose() {
    _api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: Colors.transparent,
        floatingActionButton: isAdmin ? FloatingActionButton(onPressed: _create, child: const Icon(Icons.add_alert)) : null,
        body: AsyncList(
          future: _future,
          onRefresh: _reload,
          empty: '현재 활성 안전 알림이 없습니다',
          item: (a) {
            final (label, color) = _severity[a['severity']] ?? _severity['info']!;
            final section = [a['station_from'], a['station_to']].where((s) => '${s ?? ''}'.isNotEmpty).join(' → ');
            return InfoCard(
              leading: Icon(Icons.warning_amber_rounded, color: color),
              title: '[$label] ${a['message']}',
              subtitle: [section, shortTime(a['created_at'])].where((s) => s.isNotEmpty).join(' · '),
              trailing: isAdmin
                  ? IconButton(
                      tooltip: '내리기',
                      icon: const Icon(Icons.close),
                      onPressed: () async {
                        if (await runAction(context, () => _api.deleteAlert('${a['id']}'))) _reload();
                      },
                    )
                  : null,
            );
          },
        ),
      );
}

class _HazardsTab extends StatefulWidget {
  const _HazardsTab();
  @override
  State<_HazardsTab> createState() => _HazardsTabState();
}

class _HazardsTabState extends State<_HazardsTab> {
  final _api = LifeApi();
  String? _category;
  late Future<List<Json>> _future = _api.fetchHazards();

  Future<void> _reload() async {
    setState(() => _future = _api.fetchHazards(category: _category));
    await _future.catchError((_) => <Json>[]);
  }

  Future<void> _create() async {
    var category = _category ?? 'hazard';
    final v = await promptFields(context, '${_categories[category]} 신고', ['제목', '위치 (역·구간)', '내용'], maxLines: 5);
    if (v == null || !mounted || v[0].isEmpty || v[2].isEmpty) return;
    final ok = await runAction(
      context,
      () => _api.createHazard({'category': category, 'title': v[0], 'location': v[1], 'description': v[2]}),
      done: '신고했습니다',
    );
    if (ok) _reload();
  }

  @override
  void dispose() {
    _api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: Colors.transparent,
        floatingActionButton: FloatingActionButton.extended(onPressed: _create, icon: const Icon(Icons.edit), label: const Text('신고')),
        body: Column(children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: Wrap(spacing: 8, children: [
              for (final entry in {null: '전체', ..._categories}.entries)
                ChoiceChip(
                  label: Text(entry.value),
                  selected: _category == entry.key,
                  onSelected: (_) {
                    _category = entry.key;
                    _reload();
                  },
                ),
            ]),
          ),
          Expanded(
            child: AsyncList(
              future: _future,
              onRefresh: _reload,
              empty: '접수된 신고가 없습니다',
              item: (h) => InfoCard(
                title: h['title'] ?? '',
                subtitle: '${_categories[h['category']] ?? ''} · ${h['location'] ?? ''} · ${h['author_name'] ?? ''} · 댓글 ${h['comment_count'] ?? 0}',
                trailing: Chip(label: Text(_statuses[h['status']] ?? '${h['status']}')),
                onTap: () async {
                  await Navigator.push(context, MaterialPageRoute(builder: (_) => _HazardDetail(id: '${h['id']}')));
                  _reload();
                },
              ),
            ),
          ),
        ]),
      );
}

class _HazardDetail extends StatefulWidget {
  const _HazardDetail({required this.id});
  final String id;
  @override
  State<_HazardDetail> createState() => _HazardDetailState();
}

class _HazardDetailState extends State<_HazardDetail> {
  final _api = LifeApi();
  final _comment = TextEditingController();
  late Future<Json> _future = _api.fetchHazard(widget.id);

  void _reload() => setState(() => _future = _api.fetchHazard(widget.id));

  @override
  void dispose() {
    _api.close();
    _comment.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => lifeScaffold(
        '신고 상세',
        FutureBuilder<Json>(
          future: _future,
          builder: (context, snap) {
            if (snap.hasError) return Center(child: Text('불러오지 못했습니다\n${snap.error}', textAlign: TextAlign.center));
            if (!snap.hasData) return const Center(child: CircularProgressIndicator());
            final h = snap.data!;
            final comments = (h['comments'] as List? ?? []).cast<Json>();
            return Column(children: [
              Expanded(
                child: ListView(padding: const EdgeInsets.all(16), children: [
                  Text(h['title'] ?? '', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: AppColors.ink)),
                  const SizedBox(height: 6),
                  Text('${_categories[h['category']] ?? ''} · ${h['location'] ?? ''} · ${h['author_name'] ?? ''} · ${shortTime(h['created_at'])}',
                      style: TextStyle(color: AppColors.secondaryInk)),
                  const SizedBox(height: 12),
                  Text(h['description'] ?? '', style: TextStyle(color: AppColors.ink, height: 1.5)),
                  const SizedBox(height: 12),
                  Wrap(spacing: 8, children: [
                    for (final s in _statuses.entries)
                      ChoiceChip(
                        label: Text(s.value),
                        selected: h['status'] == s.key,
                        onSelected: isAdmin
                            ? (_) async {
                                if (await runAction(context, () => _api.updateHazardStatus(widget.id, s.key))) _reload();
                              }
                            : null,
                      ),
                  ]),
                  const Divider(height: 32),
                  Text('댓글 ${comments.length}', style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.ink)),
                  for (final c in comments)
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: Text(c['content'] ?? ''),
                      subtitle: Text('${c['author_name'] ?? ''} · ${shortTime(c['created_at'])}'),
                    ),
                ]),
              ),
              SafeArea(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 4, 8, 8),
                  child: Row(children: [
                    Expanded(child: TextField(controller: _comment, decoration: const InputDecoration(hintText: '댓글 쓰기'))),
                    IconButton(
                      icon: const Icon(Icons.send),
                      onPressed: () async {
                        final text = _comment.text.trim();
                        if (text.isEmpty) return;
                        if (await runAction(context, () => _api.addHazardComment(widget.id, text))) {
                          _comment.clear();
                          _reload();
                        }
                      },
                    ),
                  ]),
                ),
              ),
            ]);
          },
        ),
      );
}

class _TipsTab extends StatefulWidget {
  const _TipsTab();
  @override
  State<_TipsTab> createState() => _TipsTabState();
}

class _TipsTabState extends State<_TipsTab> {
  final _api = LifeApi();
  late Future<List<Json>> _future = _api.fetchTips();

  Future<void> _reload() async {
    setState(() => _future = _api.fetchTips());
    await _future.catchError((_) => <Json>[]);
  }

  @override
  void dispose() {
    _api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: Colors.transparent,
        floatingActionButton: isAdmin
            ? FloatingActionButton(
                child: const Icon(Icons.add),
                onPressed: () async {
                  final v = await promptFields(context, '안전상식 등록', ['제목', '자료 링크 (선택)', '내용'], maxLines: 6);
                  if (v == null || !context.mounted || v[0].isEmpty) return;
                  final ok = await runAction(context,
                      () => _api.createTip({'title': v[0], 'media_url': v[1].isEmpty ? null : v[1], 'description': v[2]}));
                  if (ok) _reload();
                },
              )
            : null,
        body: AsyncList(
          future: _future,
          onRefresh: _reload,
          empty: '등록된 안전상식이 없습니다',
          item: (t) => Card(
            elevation: 0,
            color: AppColors.card,
            child: ExpansionTile(
              title: Text(t['title'] ?? '', style: const TextStyle(fontWeight: FontWeight.w700)),
              childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              expandedCrossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(t['description'] ?? ''),
                if (t['media_url'] != null) SelectableText('${t['media_url']}', style: TextStyle(color: AppColors.evidence)),
                if (isAdmin)
                  TextButton(
                    onPressed: () async {
                      if (await runAction(context, () => _api.deleteTip('${t['id']}'))) _reload();
                    },
                    child: const Text('삭제'),
                  ),
              ],
            ),
          ),
        ),
      );
}
