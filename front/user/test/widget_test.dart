import 'package:user/app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:user/data/chat_models.dart';
import 'package:user/data/conversation_store.dart';

Future<void> pumpLoggedInApp(WidgetTester tester) async {
  SharedPreferences.setMockInitialValues({});
  await tester.runAsync(() => ConversationStore.instance.load('test'));
  await tester.pumpWidget(const MaterialApp(home: AppShell()));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('shows Da-Al-G home experience', (tester) async {
    await pumpLoggedInApp(tester);

    expect(find.text('오늘의 승무 지원'), findsOneWidget);
    expect(find.text('규정 본문'), findsOneWidget);
    expect(find.text('준비 중'), findsNothing);
  });

  testWidgets('new user starts with an empty chat history', (tester) async {
    await pumpLoggedInApp(tester);

    expect(ConversationStore.instance.conversations, isEmpty);
  });

  testWidgets('chat room shows sources, feedback and disclaimer', (tester) async {
    await pumpLoggedInApp(tester);
    ConversationStore.instance.addOrUpdate(
      Conversation(
        id: 'c1',
        title: '출입문 고장 시 승객 안내',
        createdAt: DateTime.now(),
        messages: [
          ChatMsg(isUser: true, text: '출입문 고장 시 승객 안내'),
          ChatMsg(
            isUser: false,
            text: '답변',
            sources: [
              ChatSource(regulation: '운전취급규정', chapter: '제1조', version: ''),
              ChatSource(regulation: '안전관리규정', chapter: '제2조', version: '', retriever: '그래프 1 hop'),
            ],
          ),
        ],
      ),
    );

    await tester.tap(find.byIcon(Icons.chat_bubble_outline_rounded));
    await tester.pumpAndSettle();
    expect(find.text('규정 AI 도우미'), findsOneWidget);

    await tester.tap(find.text('출입문 고장 시 승객 안내').first);
    await tester.pumpAndSettle();

    expect(find.text('근거 2건 · 옆으로 넘겨 보기'), findsOneWidget);
    expect(find.text('관련 조항'), findsOneWidget);
    expect(find.byIcon(Icons.thumb_down_outlined), findsOneWidget);
    expect(find.text('AI 답변은 참고용입니다. 공식 규정집이 우선합니다.'), findsOneWidget);
  });
}
