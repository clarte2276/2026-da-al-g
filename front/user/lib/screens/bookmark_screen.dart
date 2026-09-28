import 'package:flutter/material.dart';
import '../core/bookmark_store.dart';
import '../core/colors.dart';
import '../widgets/app_card.dart';
import '../widgets/app_page.dart';
import '../widgets/page_header.dart';
import 'regulation_viewer_screen.dart';

class BookmarkScreen extends StatefulWidget {
  const BookmarkScreen({super.key});

  @override
  State<BookmarkScreen> createState() => _BookmarkScreenState();
}

class _BookmarkScreenState extends State<BookmarkScreen> {
  final store = BookmarkStore.instance;

  @override
  void initState() {
    super.initState();
    store.ensureLoaded();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('보관함')),
      body: AnimatedBuilder(
        animation: store,
        builder: (context, _) {
          final items = store.items;
          return AppPage(
            children: [
              const PageHeader(title: '보관함', eyebrow: '저장한 규정 조항'),
              if (items.isEmpty)
                const _EmptyState()
              else
                AppCard(
                  padding: EdgeInsets.zero,
                  child: Column(
                    children: [
                      for (var i = 0; i < items.length; i++) ...[
                        if (i > 0) const Divider(height: 1, indent: 56),
                        ListTile(
                          leading: const Icon(Icons.bookmark_rounded, color: AppColors.line6Gold),
                          title: Text(items[i].regulation,
                              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
                          subtitle: Text(items[i].chapter, style: const TextStyle(fontSize: 12)),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(items[i].version,
                                  style: TextStyle(color: AppColors.ghostText, fontSize: 11)),
                              IconButton(
                                tooltip: '삭제',
                                icon: Icon(Icons.close_rounded, size: 18, color: AppColors.ghostText),
                                onPressed: () => store.remove(items[i]),
                              ),
                            ],
                          ),
                          onTap: () => Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => RegulationViewerScreen(source: items[i]),
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 80),
      child: Column(
        children: [
          Icon(Icons.bookmark_border_rounded, size: 56, color: AppColors.ghostText),
          const SizedBox(height: 12),
          const Text('저장된 조항이 없습니다',
              style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
          const SizedBox(height: 6),
          Text('규정 원문 화면에서 북마크 아이콘을 탭하면\n여기에 저장됩니다.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.secondaryInk, fontSize: 13, height: 1.5)),
        ],
      ),
    );
  }
}
