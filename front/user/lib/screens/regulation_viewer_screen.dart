import 'dart:typed_data';

import 'package:flutter/material.dart';
import '../core/bookmark_store.dart';
import '../core/colors.dart';
import '../data/chat_models.dart';
import '../services/ai_api_client.dart';
import '../widgets/app_card.dart';
import '../widgets/app_page.dart';
import '../widgets/page_header.dart';

class RegulationViewerScreen extends StatelessWidget {
  const RegulationViewerScreen({super.key, this.source});

  final ChatSource? source;

  @override
  Widget build(BuildContext context) {
    final title = source?.regulation ?? '원문';
    final chapter = source?.chapter ?? '선택된 근거 없음';
    final sourcePath = source?.sourcePath;
    final content = source?.content?.trim().isNotEmpty == true
        ? source!.content!.trim()
        : source?.excerpt?.trim();

    final store = BookmarkStore.instance;

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(title, maxLines: 1, overflow: TextOverflow.ellipsis),
        actions: [
          if (source != null)
            AnimatedBuilder(
              animation: store,
              builder: (context, _) {
                final saved = store.isBookmarked(source!);
                return IconButton(
                  tooltip: saved ? '보관함에서 제거' : '보관함에 저장',
                  icon: Icon(
                    saved ? Icons.bookmark_rounded : Icons.bookmark_border_rounded,
                    color: AppColors.line6Gold,
                  ),
                  onPressed: () {
                    final added = store.toggle(source!);
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        duration: const Duration(seconds: 1),
                        content: Text(added ? '보관함에 저장했습니다.' : '보관함에서 제거했습니다.'),
                      ),
                    );
                  },
                );
              },
            ),
        ],
      ),
      body: AppPage(
        children: [
          PageHeader(
            title: chapter,
            eyebrow: sourcePath == null || sourcePath.isEmpty
                ? 'data 원문'
                : sourcePath,
          ),
          if (source?.documentId != null) ...[
            _PageImage(source: source!, quote: content),
            const SizedBox(height: 16),
          ],
          AppCard(
            background: AppColors.softEvidence,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 16,
                  ),
                ),
                if (source?.page != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    '${source!.page}쪽',
                    style: TextStyle(
                      color: AppColors.secondaryInk,
                      fontSize: 13,
                    ),
                  ),
                ],
                const SizedBox(height: 14),
                SelectableText(
                  content == null || content.isEmpty
                      ? '이 답변에는 표시할 원문 본문이 없습니다.'
                      : content,
                  style: TextStyle(
                    color: AppColors.ink,
                    fontSize: 14,
                    height: 1.6,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// 근거가 있는 원문 페이지 이미지. 실패하면 아래 텍스트만 남는다.
class _PageImage extends StatefulWidget {
  const _PageImage({required this.source, this.quote});

  final ChatSource source;
  final String? quote;

  @override
  State<_PageImage> createState() => _PageImageState();
}

class _PageImageState extends State<_PageImage> {
  final _client = AiApiClient();
  late final Future<Uint8List> _image = _client.fetchPageImage(
    widget.source.documentId!,
    versionId: widget.source.versionId,
    page: widget.source.page,
    quote: widget.quote,
  );

  @override
  void dispose() {
    _client.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Uint8List>(
      future: _image,
      builder: (context, snapshot) {
        if (snapshot.hasData) {
          return ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: InteractiveViewer(
              maxScale: 5,
              child: Image.memory(snapshot.data!, fit: BoxFit.fitWidth),
            ),
          );
        }
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 24),
          child: Center(
            child: snapshot.hasError
                ? Text(
                    '원문 페이지를 불러오지 못했습니다.\n아래 본문으로 확인해 주세요.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: AppColors.secondaryInk, fontSize: 13),
                  )
                : const CircularProgressIndicator(),
          ),
        );
      },
    );
  }
}
