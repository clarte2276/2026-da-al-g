import 'package:flutter/material.dart';

import '../core/models/rag_models.dart';
import '../core/services/rag_api_client.dart';
import 'source_page_view.dart';

class EvidenceList extends StatelessWidget {
  const EvidenceList({required this.response, this.api, super.key});

  final ChatResponse response;
  final RagApiClient? api;

  @override
  Widget build(BuildContext context) {
    if (response.mode == 'general' && response.evidence.isEmpty) {
      return const SizedBox.shrink();
    }
    final colorScheme = Theme.of(context).colorScheme;
    return Column(
      children: [
        const SizedBox(height: 10),
        Wrap(
          spacing: 6,
          runSpacing: 6,
          children: [
            _MetaChip(
              Icons.menu_book_rounded,
              response.mode == 'insufficient_evidence'
                  ? '관련 문서 근거 없음'
                  : '근거 ${response.evidence.length}개',
            ),
            if (response.graphExpanded)
              _MetaChip(Icons.account_tree_rounded, '그래프 확장됨'),
            _MetaChip(Icons.memory_rounded, response.embeddingProvider),
          ],
        ),
        if (response.evidence.isNotEmpty) ...[
          const SizedBox(height: 4),
          Theme(
            data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
            child: ExpansionTile(
              tilePadding: EdgeInsets.zero,
              childrenPadding: EdgeInsets.zero,
              leading: Icon(Icons.source_rounded, color: colorScheme.primary),
              title: const Text('검색 근거 보기'),
              subtitle: const Text('답변에 사용된 문서 조각'),
              children: response.evidence
                  .asMap()
                  .entries
                  .map(
                    (entry) => EvidenceCard(
                      number: entry.key + 1,
                      evidence: entry.value,
                      api: api,
                    ),
                  )
                  .toList(),
            ),
          ),
        ],
      ],
    );
  }
}

class _MetaChip extends StatelessWidget {
  const _MetaChip(this.icon, this.label);

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Chip(
      avatar: Icon(icon, size: 15, color: colorScheme.primary),
      label: Text(label),
      visualDensity: VisualDensity.compact,
      side: BorderSide.none,
      backgroundColor: colorScheme.primaryContainer,
      labelStyle: TextStyle(
        color: colorScheme.onPrimaryContainer,
        fontSize: 12,
      ),
    );
  }
}

class EvidenceCard extends StatelessWidget {
  const EvidenceCard({
    required this.number,
    required this.evidence,
    this.api,
    super.key,
  });

  final int number;
  final RagEvidence evidence;
  final RagApiClient? api;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 12,
                backgroundColor: colorScheme.primary,
                child: Text(
                  '$number',
                  style: TextStyle(color: colorScheme.onPrimary, fontSize: 12),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      evidence.sourceLabel,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                    Text(
                      '${evidence.locationLabel} · ${evidence.originLabel} · 점수 ${evidence.score.toStringAsFixed(2)}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
              if (evidence.viaRelation != null)
                Text(
                  evidence.viaRelation!,
                  style: TextStyle(fontSize: 11, color: colorScheme.primary),
                ),
            ],
          ),
          if (evidence.text.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(evidence.text, style: const TextStyle(height: 1.45)),
          ],
          if (api != null && evidence.hasSource)
            Align(
              alignment: Alignment.centerLeft,
              child: TextButton.icon(
                icon: const Icon(Icons.picture_as_pdf_rounded, size: 18),
                label: const Text('원문 페이지 보기'),
                onPressed: () => showSourcePage(context, api!, evidence),
              ),
            ),
          if (evidence.linkId != null)
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text(
                '승인된 문서 연결을 통해 확장된 근거',
                style: TextStyle(fontSize: 11, color: colorScheme.primary),
              ),
            ),
        ],
      ),
    );
  }
}
