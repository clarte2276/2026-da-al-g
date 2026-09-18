import 'package:flutter/material.dart';

import '../core/models/rag_models.dart';
import '../core/services/rag_api_client.dart';
import 'evidence_list.dart';

class ChatMessageBubble extends StatelessWidget {
  const ChatMessageBubble({required this.message, this.api, super.key});

  final ChatMessage message;
  final RagApiClient? api;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final isUser = message.isUser;
    final bubbleColor = isUser
        ? colorScheme.primary
        : message.isError
        ? colorScheme.errorContainer
        : colorScheme.surface;
    final textColor = isUser
        ? colorScheme.onPrimary
        : message.isError
        ? colorScheme.onErrorContainer
        : colorScheme.onSurface;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.sizeOf(context).width * 0.84,
        ),
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.fromLTRB(16, 13, 16, 10),
        decoration: BoxDecoration(
          color: bubbleColor,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(18),
            topRight: const Radius.circular(18),
            bottomLeft: Radius.circular(isUser ? 18 : 4),
            bottomRight: Radius.circular(isUser ? 4 : 18),
          ),
          boxShadow: isUser
              ? null
              : const [
                  BoxShadow(
                    color: Color(0x0D172554),
                    blurRadius: 12,
                    offset: Offset(0, 4),
                  ),
                ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (!isUser)
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      message.isError
                          ? Icons.error_outline_rounded
                          : Icons.auto_awesome_rounded,
                      size: 16,
                      color: message.isError ? textColor : colorScheme.primary,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      message.isError ? '오류' : 'Da-Al-G AI',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: textColor,
                      ),
                    ),
                  ],
                ),
              ),
            SelectableText(
              message.text,
              style: TextStyle(color: textColor, height: 1.5, fontSize: 15),
            ),
            if (message.response != null)
              EvidenceList(response: message.response!, api: api),
          ],
        ),
      ),
    );
  }
}

class LoadingBubble extends StatelessWidget {
  const LoadingBubble({super.key});

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: colorScheme.surface,
          borderRadius: BorderRadius.circular(18),
          boxShadow: const [
            BoxShadow(
              color: Color(0x0D172554),
              blurRadius: 12,
              offset: Offset(0, 4),
            ),
          ],
        ),
        child: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            SizedBox(width: 10),
            Text('답변을 준비하는 중...'),
          ],
        ),
      ),
    );
  }
}
