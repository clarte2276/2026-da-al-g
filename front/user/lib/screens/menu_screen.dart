import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../core/colors.dart';
import '../services/life_api.dart';
import 'life_common.dart';

/// ISO 주차 (예: 2026-W41).
String isoWeek(DateTime d) {
  final thursday = d.add(Duration(days: 4 - d.weekday));
  final week = ((thursday.difference(DateTime(thursday.year)).inDays) ~/ 7) + 1;
  return '${thursday.year}-W${week.toString().padLeft(2, '0')}';
}

class MenuScreen extends StatefulWidget {
  const MenuScreen({super.key});
  @override
  State<MenuScreen> createState() => _MenuScreenState();
}

class _MenuScreenState extends State<MenuScreen> {
  final _api = LifeApi();
  late Future<List<Json>> _future = _api.fetchMenus();

  Future<void> _reload() async {
    setState(() => _future = _api.fetchMenus());
    await _future.catchError((_) => <Json>[]);
  }

  Future<void> _upload() async {
    final picked = await ImagePicker().pickImage(source: ImageSource.gallery, imageQuality: 85);
    if (picked == null || !mounted) return;
    final v = await promptFields(context, '식단표 주차', ['주차 (예: 2026-W41)'], initial: [isoWeek(DateTime.now())]);
    if (v == null || v[0].isEmpty || !mounted) return;
    final bytes = await picked.readAsBytes();
    if (!mounted) return;
    if (await runAction(context, () => _api.uploadMenu(v[0], picked.name, bytes), done: '올렸습니다')) _reload();
  }

  @override
  void dispose() {
    _api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => lifeScaffold(
        '식당 메뉴',
        AsyncList(
          future: _future,
          onRefresh: _reload,
          empty: '등록된 식단표가 없습니다',
          item: (m) {
            final isPdf = '${m['filename']}'.toLowerCase().endsWith('.pdf');
            return Card(
              elevation: 0,
              color: AppColors.card,
              clipBehavior: Clip.antiAlias,
              child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                ListTile(
                  title: Text('${m['week']}${m['week'] == isoWeek(DateTime.now()) ? ' (이번 주)' : ''}',
                      style: const TextStyle(fontWeight: FontWeight.w800)),
                  subtitle: Text('${m['filename']}'),
                ),
                if (isPdf)
                  const Padding(padding: EdgeInsets.all(16), child: Text('PDF 식단표는 관리자 화면에서 확인하세요'))
                else
                  InteractiveViewer(
                    maxScale: 4,
                    child: Image.network(
                      _api.menuFileUrl('${m['id']}'),
                      headers: _api.authHeaders,
                      errorBuilder: (_, _, _) => const Padding(padding: EdgeInsets.all(16), child: Text('이미지를 불러오지 못했습니다')),
                    ),
                  ),
              ]),
            );
          },
        ),
        fab: isAdmin ? FloatingActionButton(onPressed: _upload, child: const Icon(Icons.upload)) : null,
      );
}
