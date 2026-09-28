import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../services/ai_api_client.dart';
import '../widgets/skeleton.dart';

/// dia5의 "규정 본문 열기"에 대응 — 규정 목록에서 원문(자료 그대로)을 본다.
class RegulationLibraryScreen extends StatefulWidget {
  const RegulationLibraryScreen({super.key});

  @override
  State<RegulationLibraryScreen> createState() => _RegulationLibraryScreenState();
}

class _RegulationLibraryScreenState extends State<RegulationLibraryScreen> {
  late Future<List<Map<String, dynamic>>> _future;

  @override
  void initState() {
    super.initState();
    final client = AiApiClient();
    _future = client.fetchRegulations().whenComplete(client.close);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(title: const Text('규정 본문', style: TextStyle(fontSize: 16))),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
              children: [
                // 카테고리 헤더 라인
                const SkeletonBox(width: 90, height: 13),
                const SizedBox(height: 24),
                // 카드 3개, 각 카드는 ListTile 형태 (52px 동그라미 + 텍스트 2줄 + chevron)
                for (var c = 0; c < 3; c++) ...[
                  Container(
                    decoration: BoxDecoration(
                      color: AppColors.card,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: Column(
                      children: [
                        for (var i = 0; i < 3; i++) ...[
                          if (i > 0) const Divider(height: 1, indent: 52),
                          const Padding(
                            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                            child: Row(
                              children: [
                                SkeletonBox(width: 52, height: 52, borderRadius: 26),
                                SizedBox(width: 16),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      SkeletonBox(height: 14),
                                      SizedBox(height: 8),
                                      SkeletonBox(width: 140, height: 12),
                                    ],
                                  ),
                                ),
                                SizedBox(width: 16),
                                SkeletonBox(width: 18, height: 18, borderRadius: 9),
                              ],
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                ],
              ],
            );
          }
          if (snap.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text('규정 목록을 불러오지 못했습니다.\n서버 연결을 확인해주세요.\n\n${snap.error}',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: AppColors.secondaryInk)),
              ),
            );
          }
          final regs = snap.data ?? const [];
          if (regs.isEmpty) {
            return Center(child: Text('등록된 규정이 없습니다.', style: TextStyle(color: AppColors.secondaryInk)));
          }
          // 분류별 그룹화
          final byCat = <String, List<Map<String, dynamic>>>{};
          for (final r in regs) {
            byCat.putIfAbsent(r['category'] as String? ?? '규정', () => []).add(r);
          }
          final cats = byCat.keys.toList()..sort();
          return ListView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
            children: [
              for (final cat in cats) ...[
                Padding(
                  padding: const EdgeInsets.fromLTRB(4, 12, 4, 8),
                  child: Text(cat,
                      style: TextStyle(
                          fontWeight: FontWeight.w800, fontSize: 13, color: AppColors.secondaryInk)),
                ),
                Container(
                  decoration: BoxDecoration(
                    color: AppColors.card,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Column(
                    children: [
                      for (var i = 0; i < byCat[cat]!.length; i++) ...[
                        if (i > 0) const Divider(height: 1, indent: 52),
                        ListTile(
                          leading: Icon(Icons.menu_book_rounded, color: AppColors.line6Gold, size: 22),
                          title: Text(byCat[cat]![i]['title'] as String? ?? '',
                              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                          trailing: Icon(Icons.chevron_right_rounded, color: AppColors.ghostText, size: 18),
                          onTap: () => Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => RegulationDocumentScreen(
                                id: byCat[cat]![i]['id'] as String,
                                title: byCat[cat]![i]['title'] as String? ?? '규정',
                              ),
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ],
          );
        },
      ),
    );
  }
}

/// 규정 원문 전체 뷰어 (자료 그대로).
class RegulationDocumentScreen extends StatefulWidget {
  const RegulationDocumentScreen({super.key, required this.id, required this.title});
  final String id;
  final String title;

  @override
  State<RegulationDocumentScreen> createState() => _RegulationDocumentScreenState();
}

class _RegulationDocumentScreenState extends State<RegulationDocumentScreen> {
  late Future<Map<String, dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = _load(widget.id);
  }

  Future<Map<String, dynamic>> _load(String id) {
    final client = AiApiClient();
    return client.fetchRegulationDocument(id).whenComplete(client.close);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(
        leading: const BackButton(),
        title: Text(widget.title, maxLines: 1, overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontSize: 16)),
      ),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            // 본문 텍스트 형태 스켈레톤: 긴 라인 5개 + 중간 라인 2개
            return ListView(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
              children: [
                for (var i = 0; i < 5; i++) ...[
                  const SkeletonBox(height: 14),
                  const SizedBox(height: 10),
                ],
                const SizedBox(height: 12),
                const SkeletonBox(width: 200, height: 14),
                const SizedBox(height: 10),
                const SkeletonBox(width: 150, height: 14),
              ],
            );
          }
          if (snap.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text('원문을 불러오지 못했습니다.\n\n${snap.error}',
                    textAlign: TextAlign.center, style: TextStyle(color: AppColors.secondaryInk)),
              ),
            );
          }
          final doc = snap.data!;
          final content = (doc['content'] as String? ?? '').trim();
          final annexes = (doc['annexes'] as List? ?? const [])
              .whereType<Map<String, dynamic>>()
              .toList();
          return ListView(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
            children: [
              SelectableText(
                content.isEmpty ? '본문이 없습니다.' : content,
                style: TextStyle(color: AppColors.ink, fontSize: 14, height: 1.7),
              ),
              if (annexes.isNotEmpty) ...[
                const SizedBox(height: 24),
                Text('부속 서류 (별표·별지)',
                    style: TextStyle(fontWeight: FontWeight.w800, fontSize: 13, color: AppColors.secondaryInk)),
                const SizedBox(height: 8),
                for (final a in annexes)
                  ListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    leading: Icon(Icons.attach_file_rounded, size: 18, color: AppColors.evidence),
                    title: Text(a['title'] as String? ?? '', style: const TextStyle(fontSize: 13)),
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => RegulationDocumentScreen(
                          id: a['id'] as String,
                          title: a['title'] as String? ?? '부속서류',
                        ),
                      ),
                    ),
                  ),
              ],
            ],
          );
        },
      ),
    );
  }
}
