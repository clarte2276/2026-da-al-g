import 'package:flutter/material.dart';

class BoardPost extends StatelessWidget {
  const BoardPost({
    super.key,
    required this.title,
    required this.meta,
    required this.commentCount,
    required this.onTap,
  });
  final String title, meta;
  final int commentCount;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
      subtitle: Text(meta, style: const TextStyle(fontSize: 12)),
      trailing: commentCount > 0
          ? Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.chat_bubble_outline, size: 12),
                const SizedBox(width: 4),
                Text('$commentCount'),
              ],
            )
          : null,
      onTap: onTap,
    );
  }
}
