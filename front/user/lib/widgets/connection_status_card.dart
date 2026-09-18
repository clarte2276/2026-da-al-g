import 'package:flutter/material.dart';

class ConnectionStatusCard extends StatelessWidget {
  const ConnectionStatusCard({
    required this.baseUrl,
    required this.provider,
    required this.checking,
    required this.error,
    required this.onCheck,
    super.key,
  });

  final String baseUrl;
  final String? provider;
  final bool checking;
  final String? error;
  final VoidCallback onCheck;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final status = checking
        ? '연결 확인 중'
        : error != null
        ? '연결 실패'
        : provider == null
        ? '서버 연결 전'
        : '연결됨 · $provider';
    final statusColor = error != null
        ? colorScheme.error
        : provider == null
        ? colorScheme.onSurfaceVariant
        : colorScheme.primary;

    return Container(
      margin: const EdgeInsets.fromLTRB(16, 12, 16, 4),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: colorScheme.outlineVariant),
      ),
      child: Row(
        children: [
          Icon(Icons.cloud_outlined, size: 20, color: statusColor),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  status,
                  style: TextStyle(
                    fontWeight: FontWeight.w700,
                    color: statusColor,
                  ),
                ),
                Text(
                  baseUrl,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          TextButton(onPressed: onCheck, child: const Text('확인')),
        ],
      ),
    );
  }
}
