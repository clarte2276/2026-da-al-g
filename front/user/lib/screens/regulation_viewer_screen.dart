import 'package:flutter/material.dart';
import '../core/bookmark_store.dart';
import '../core/colors.dart';
import '../data/mock_conversations.dart';
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
                if (source?.retriever != null || source?.chunkId != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    [
                      if (source?.retriever != null) source!.retriever!,
                      if (source?.chunkId != null) source!.chunkId!,
                    ].join(' · '),
                    style: TextStyle(
                      color: AppColors.secondaryInk,
                      fontSize: 12,
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
