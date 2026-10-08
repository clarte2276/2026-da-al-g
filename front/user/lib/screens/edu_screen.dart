import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../services/life_api.dart';
import 'life_common.dart';

/// 교육 영상: 분류별로 묶어 보여주고 외부 링크로 연다.
class EduScreen extends StatefulWidget {
  const EduScreen({super.key});
  @override
  State<EduScreen> createState() => _EduScreenState();
}

class _EduScreenState extends State<EduScreen> {
  final _api = LifeApi();
  late Future<List<Json>> _future = _load();

  /// 분류별 묶음을 한 목록으로 펼친다: 분류 머리글 행 + 영상 행.
  Future<List<Json>> _load() => _api.fetchEduVideos().then((videos) {
    final byCategory = <String, List<Json>>{};
    for (final v in videos) {
      byCategory.putIfAbsent('${v['category']}', () => []).add(v);
    }
    return [
      for (final e in byCategory.entries) ...[
        {'header': e.key},
        ...e.value,
      ],
    ];
  });

  Future<void> _reload() async {
    setState(() => _future = _load());
    await _future.catchError((_) => <Json>[]);
  }

  Future<void> _add() async {
    final v = await promptFields(context, '교육 영상 등록', ['분류 (예: 고장조치)', '제목', '링크 (https://…)']);
    if (v == null || v.any((s) => s.isEmpty) || !mounted) return;
    if (await runAction(context, () => _api.createEduVideo({'category': v[0], 'title': v[1], 'url': v[2]}))) _reload();
  }

  @override
  void dispose() {
    _api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => lifeScaffold(
    '교육 영상',
    AsyncList(
      future: _future,
      onRefresh: _reload,
      empty: '등록된 교육 영상이 없습니다',
      item: (v) => v.containsKey('header')
          ? Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                '${v['header']}',
                style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.secondaryInk),
              ),
            )
          : InfoCard(
              leading: const Icon(Icons.play_circle_outline),
              title: '${v['title']}',
              onTap: () => openLink(context, '${v['url']}'),
              trailing: isAdmin
                  ? IconButton(
                      icon: const Icon(Icons.delete_outline),
                      onPressed: () async {
                        if (await runAction(context, () => _api.deleteEduVideo('${v['id']}'))) _reload();
                      },
                    )
                  : null,
            ),
    ),
    fab: isAdmin ? FloatingActionButton(onPressed: _add, child: const Icon(Icons.add)) : null,
  );
}
