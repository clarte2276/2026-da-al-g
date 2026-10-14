import 'package:flutter/material.dart';

import '../core/colors.dart';
import '../services/ai_api_client.dart';

class DiaImage extends StatelessWidget {
  const DiaImage({
    super.key,
    required this.path,
    this.width,
    this.loadingColor = AppColors.line6Gold,
    this.errorColor = Colors.white70,
  });

  final String path;
  final double? width;
  final Color loadingColor;
  final Color errorColor;

  @override
  Widget build(BuildContext context) => Image.network(
    '${AiApiClient.defaultBaseUrl}$path',
    headers: AiApiClient.authorizationHeaders,
    width: width,
    loadingBuilder: (context, child, progress) => progress == null
        ? child
        : Padding(
            padding: const EdgeInsets.all(24),
            child: CircularProgressIndicator(color: loadingColor),
          ),
    errorBuilder: (context, error, stackTrace) => Padding(
      padding: const EdgeInsets.all(24),
      child: Text('운전표를 불러오지 못했습니다.', style: TextStyle(color: errorColor)),
    ),
  );
}

Future<void> showDiaImageViewer(BuildContext context, String path) =>
    Navigator.of(context).push(
      MaterialPageRoute<void>(builder: (_) => _DiaImageViewer(path: path)),
    );

class _DiaImageViewer extends StatelessWidget {
  const _DiaImageViewer({required this.path});

  final String path;

  @override
  Widget build(BuildContext context) {
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
          child: DiaImage(path: path),
        ),
      ),
    );
  }
}
