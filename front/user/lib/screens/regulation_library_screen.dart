import 'dart:typed_data';

import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../services/ai_api_client.dart';
import '../widgets/skeleton.dart';

/// 규정 목록. 원본 자료(data_pdf)와 같은 폴더 구조로 탐색한다.
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
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) {
          return const _FolderScaffold(title: '규정 본문', body: _ListSkeleton());
        }
        if (snap.hasError) {
          return _FolderScaffold(
            title: '규정 본문',
            body: Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text('규정 목록을 불러오지 못했습니다.\n서버 연결을 확인해 주세요.',
                    textAlign: TextAlign.center, style: TextStyle(color: AppColors.secondaryInk)),
              ),
            ),
          );
        }
        return RegulationFolderView(docs: snap.data ?? const [], path: const []);
      },
    );
  }
}

/// 한 폴더의 하위 폴더와 문서. 폴더를 누르면 한 단계 안으로 들어간다.
class RegulationFolderView extends StatelessWidget {
  const RegulationFolderView({super.key, required this.docs, required this.path});
  final List<Map<String, dynamic>> docs;
  final List<String> path;

  List<String> _segments(Map<String, dynamic> doc) =>
      (doc['folder'] as String? ?? '').split('/').where((s) => s.isNotEmpty).toList();

  bool _under(List<String> segments) =>
      segments.length >= path.length &&
      Iterable.generate(path.length).every((i) => segments[i] == path[i]);

  @override
  Widget build(BuildContext context) {
    final folders = <String>{};
    final files = <Map<String, dynamic>>[];
    for (final doc in docs) {
      final segments = _segments(doc);
      if (!_under(segments)) continue;
      if (segments.length == path.length) {
        files.add(doc);
      } else {
        folders.add(segments[path.length]);
      }
    }
    final sortedFolders = folders.toList()..sort();
    // 본 규정을 먼저, [별표]·[별지] 서식은 뒤에.
    files.sort((x, y) {
      final a = x['title'] as String? ?? '', b = y['title'] as String? ?? '';
      final byAnnex = (a.startsWith('[') ? 1 : 0).compareTo(b.startsWith('[') ? 1 : 0);
      return byAnnex != 0 ? byAnnex : a.compareTo(b);
    });

    final tiles = <Widget>[
      for (final name in sortedFolders)
        ListTile(
          leading: Icon(Icons.folder_rounded, color: AppColors.line6Gold, size: 22),
          title: Text(name, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
          trailing: Icon(Icons.chevron_right_rounded, color: AppColors.ghostText, size: 18),
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => RegulationFolderView(docs: docs, path: [...path, name])),
          ),
        ),
      for (final doc in files)
        ListTile(
          leading: Icon(Icons.description_outlined, color: AppColors.evidence, size: 22),
          title: Text(doc['title'] as String? ?? '',
              style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 14)),
          trailing: Icon(Icons.chevron_right_rounded, color: AppColors.ghostText, size: 18),
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => RegulationDocumentScreen(
                id: doc['id'] as String,
                title: doc['title'] as String? ?? '규정',
              ),
            ),
          ),
        ),
    ];

    return _FolderScaffold(
      title: path.isEmpty ? '규정 본문' : path.last,
      body: tiles.isEmpty
          ? Center(child: Text('등록된 규정이 없습니다.', style: TextStyle(color: AppColors.secondaryInk)))
          : ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
              children: [
                if (path.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.fromLTRB(4, 4, 4, 10),
                    child: Text(path.join(' › '),
                        style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)),
                  ),
                Material(
                  color: AppColors.card,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                    side: BorderSide(color: AppColors.border),
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: Column(
                    children: [
                      for (var i = 0; i < tiles.length; i++) ...[
                        if (i > 0) const Divider(height: 1, indent: 56),
                        tiles[i],
                      ],
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}

class _FolderScaffold extends StatelessWidget {
  const _FolderScaffold({required this.title, required this.body});
  final String title;
  final Widget body;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(title: Text(title, style: const TextStyle(fontSize: 16))),
      body: body,
    );
  }
}

class _ListSkeleton extends StatelessWidget {
  const _ListSkeleton();

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
      children: [
        for (var i = 0; i < 6; i++)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 10),
            child: Row(
              children: [
                SkeletonBox(width: 24, height: 24, borderRadius: 6),
                SizedBox(width: 16),
                Expanded(child: SkeletonBox(height: 14)),
              ],
            ),
          ),
      ],
    );
  }
}

/// 규정 원문 뷰어: 원본을 PDF로 렌더한 페이지를 위에서 아래로 보여준다.
/// PDF 변환에 실패하면 추출 텍스트로 대신 보여준다.
class RegulationDocumentScreen extends StatefulWidget {
  const RegulationDocumentScreen({super.key, required this.id, required this.title});
  final String id;
  final String title;

  @override
  State<RegulationDocumentScreen> createState() => _RegulationDocumentScreenState();
}

class _RegulationDocumentScreenState extends State<RegulationDocumentScreen> {
  final _client = AiApiClient();
  late final Future<int> _pageCount = _client.fetchPageCount(widget.id);

  @override
  void dispose() {
    _client.close();
    super.dispose();
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
      body: FutureBuilder<int>(
        future: _pageCount,
        builder: (context, snap) {
          if (snap.hasError) return _TextFallback(client: _client, id: widget.id);
          if (!snap.hasData) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const CircularProgressIndicator(),
                  const SizedBox(height: 12),
                  Text('원문을 여는 중… 처음 여는 문서는 1~2분 걸릴 수 있습니다.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: AppColors.secondaryInk)),
                ],
              ),
            );
          }
          final count = snap.data!;
          // 보이는 쪽만 불러온다.
          return ListView.builder(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 32),
            itemCount: count,
            itemBuilder: (_, i) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _PdfPage(client: _client, id: widget.id, page: i + 1, total: count),
            ),
          );
        },
      ),
    );
  }
}

class _PdfPage extends StatefulWidget {
  const _PdfPage({required this.client, required this.id, required this.page, required this.total});
  final AiApiClient client;
  final String id;
  final int page;
  final int total;

  @override
  State<_PdfPage> createState() => _PdfPageState();
}

class _PdfPageState extends State<_PdfPage> with AutomaticKeepAliveClientMixin {
  late final Future<Uint8List> _image = widget.client.fetchPageImage(widget.id, page: widget.page);

  // 스크롤로 벗어났다 돌아와도 다시 받지 않는다.
  @override
  bool get wantKeepAlive => true;

  @override
  Widget build(BuildContext context) {
    super.build(context);
    return Column(
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: ColoredBox(
            color: Colors.white,
            child: FutureBuilder<Uint8List>(
              future: _image,
              builder: (context, snap) {
                if (snap.hasData) {
                  return InteractiveViewer(
                    maxScale: 5,
                    child: Image.memory(snap.data!, fit: BoxFit.fitWidth, width: double.infinity),
                  );
                }
                // A4 비율 자리를 잡아 스크롤이 튀지 않게 한다.
                return AspectRatio(
                  aspectRatio: 1 / 1.414,
                  child: Center(
                    child: snap.hasError
                        ? Text('${widget.page}쪽을 불러오지 못했습니다.',
                            style: TextStyle(color: AppColors.secondaryInk))
                        : const CircularProgressIndicator(),
                  ),
                );
              },
            ),
          ),
        ),
        const SizedBox(height: 4),
        Text('${widget.page} / ${widget.total}',
            style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)),
      ],
    );
  }
}

class _TextFallback extends StatelessWidget {
  const _TextFallback({required this.client, required this.id});
  final AiApiClient client;
  final String id;

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: client.fetchRegulationDocument(id),
      builder: (context, snap) {
        if (snap.hasError) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Text('원문을 불러오지 못했습니다.',
                  textAlign: TextAlign.center, style: TextStyle(color: AppColors.secondaryInk)),
            ),
          );
        }
        if (!snap.hasData) return const Center(child: CircularProgressIndicator());
        final content = (snap.data!['content'] as String? ?? '').trim();
        return ListView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
          children: [
            Text('원문 PDF를 만들지 못해 텍스트로 보여드립니다.',
                style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)),
            const SizedBox(height: 12),
            SelectableText(
              content.isEmpty ? '본문이 없습니다.' : content,
              style: TextStyle(color: AppColors.ink, fontSize: 14, height: 1.7),
            ),
          ],
        );
      },
    );
  }
}
