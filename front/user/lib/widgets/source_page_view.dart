import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../core/models/rag_models.dart';
import '../core/services/rag_api_client.dart';

/// Show the page of the original document an evidence chunk was taken from.
Future<void> showSourcePage(
  BuildContext context,
  RagApiClient api,
  RagEvidence evidence,
) {
  return showDialog<void>(
    context: context,
    builder: (context) => Dialog(
      insetPadding: const EdgeInsets.all(16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          ListTile(
            title: Text(evidence.sourceLabel, maxLines: 2),
            subtitle: Text(evidence.locationLabel),
            trailing: IconButton(
              icon: const Icon(Icons.close_rounded),
              onPressed: () => Navigator.of(context).pop(),
            ),
          ),
          Flexible(
            child: FutureBuilder<Uint8List>(
              future: api.evidencePage(evidence),
              builder: (context, snapshot) {
                if (snapshot.connectionState != ConnectionState.done) {
                  return const Padding(
                    padding: EdgeInsets.all(48),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        CircularProgressIndicator(),
                        SizedBox(height: 12),
                        Text('원문 페이지를 준비하고 있습니다…'),
                        SizedBox(height: 4),
                        Text(
                          '문서를 처음 여는 경우 변환에 몇 분이 걸릴 수 있습니다. '
                          '창을 닫아도 변환은 계속되며, 다시 열면 바로 표시됩니다.',
                          style: TextStyle(fontSize: 12),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  );
                }
                if (snapshot.hasError) {
                  return Padding(
                    padding: const EdgeInsets.all(24),
                    child: Text('${snapshot.error}'),
                  );
                }
                return InteractiveViewer(
                  maxScale: 5,
                  child: Image.memory(snapshot.data!, fit: BoxFit.contain),
                );
              },
            ),
          ),
        ],
      ),
    ),
  );
}
