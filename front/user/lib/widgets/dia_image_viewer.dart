import 'package:flutter/material.dart';

import '../core/colors.dart';
import '../services/ai_api_client.dart';

Future<void> showDiaImageViewer(BuildContext context, String path) =>
    Navigator.of(context).push(
      MaterialPageRoute<void>(builder: (_) => _DiaImageViewer(path: path)),
    );

class _DiaImageViewer extends StatelessWidget {
  const _DiaImageViewer({required this.path});

  final String path;

  @override
  Widget build(BuildContext context) {
    final uri = Uri.parse('${AiApiClient.defaultBaseUrl}$path');
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        title: const Text('운전표'),
      ),
      body: Center(
        child: InteractiveViewer(
          minScale: 0.5,
          maxScale: 5,
          child: Image.network(
            uri.toString(),
            headers: AiApiClient.authorizationHeaders,
            loadingBuilder: (context, child, progress) => progress == null
                ? child
                : const Padding(
                    padding: EdgeInsets.all(24),
                    child: CircularProgressIndicator(
                      color: AppColors.line6Gold,
                    ),
                  ),
            errorBuilder: (context, error, stackTrace) => const Padding(
              padding: EdgeInsets.all(24),
              child: Text(
                '운전표를 불러오지 못했습니다.',
                style: TextStyle(color: Colors.white70),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
