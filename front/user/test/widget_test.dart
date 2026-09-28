import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:user/app.dart';
import 'package:user/core/models/rag_models.dart';
import 'package:user/core/services/rag_api_client.dart';
import 'package:user/pages/chat_page.dart';

class _PreviewApi extends RagApiClient {
  _PreviewApi() : super(baseUrl: 'http://localhost');

  final preview = Completer<ChatResponse>();
  final answer = Completer<ChatResponse>();

  @override
  Future<ChatResponse> previewSources(String question) => preview.future;

  @override
  Future<ChatResponse> ask(
    String message, {
    List<Map<String, String>> history = const [],
  }) => answer.future;
}

void main() {
  testWidgets('login screen is shown', (WidgetTester tester) async {
    await tester.pumpWidget(const MyApp());

    expect(find.text('Da-Al-G AI'), findsOneWidget);
    expect(find.text('로그인'), findsOneWidget);
    expect(find.text('개발 테스트 계정: test / test'), findsOneWidget);
  });

  testWidgets(
    'shows original source before replacing it with the final answer',
    (WidgetTester tester) async {
      final api = _PreviewApi();
      await tester.pumpWidget(MaterialApp(home: ChatPage(api: api)));
      await tester.enterText(find.byType(TextField), '열차 고장 조치');
      await tester.tap(find.byTooltip('질문 보내기'));
      await tester.pump();

      api.preview.complete(
        const ChatResponse(
          answer: '',
          mode: 'rag',
          evidence: [
            RagEvidence(
              text: '운전관제에 보고한다.',
              score: 1,
              hop: 0,
              filename: '운전 규정',
              fragment: null,
              location: '제1조',
            ),
          ],
          embeddingProvider: 'openai',
          graphExpanded: false,
        ),
      );
      await tester.pump();
      expect(find.text('관련 원문 후보'), findsOneWidget);
      expect(find.textContaining('운전관제에 보고한다.'), findsOneWidget);

      api.answer.complete(
        const ChatResponse(
          answer: '완성 답변입니다.',
          mode: 'rag',
          evidence: [],
          embeddingProvider: 'openai',
          graphExpanded: false,
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('완성 답변입니다.'), findsOneWidget);
      expect(find.text('관련 원문 후보'), findsNothing);
    },
  );
}
