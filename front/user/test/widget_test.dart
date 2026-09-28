import 'package:user/app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Future<void> pumpLoggedInApp(WidgetTester tester) async {
  await tester.pumpWidget(const MaterialApp(home: AppShell()));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('shows Da-Al-G home experience', (tester) async {
    await pumpLoggedInApp(tester);

    expect(find.text('오늘의 승무 지원'), findsOneWidget);
    expect(find.text('좋은 오후입니다'), findsOneWidget);
  });

  testWidgets('navigates to schedule tab and completes upload flow', (
    tester,
  ) async {
    await pumpLoggedInApp(tester);

    await tester.tap(find.byIcon(Icons.calendar_month_outlined));
    await tester.pumpAndSettle();

    expect(find.text('근무표 업로드'), findsWidgets);

    await tester.tap(find.text('샘플 파일 분석'));
    await tester.pumpAndSettle();

    expect(find.text('열차 흐름'), findsOneWidget);
    expect(find.text('출무 14:20 · 응암 → 신내'), findsOneWidget);
  });

  testWidgets('navigates to chat tab and opens chat room', (tester) async {
    await pumpLoggedInApp(tester);

    await tester.tap(find.byIcon(Icons.chat_bubble_outline_rounded));
    await tester.pumpAndSettle();

    expect(find.text('규정 AI 도우미'), findsOneWidget);

    await tester.tap(find.text('출입문 고장 시 승객 안내'));
    await tester.pumpAndSettle();

    expect(find.text('출입문 고장 시 승객 안내'), findsOneWidget);
    expect(find.text('근거 확인됨'), findsOneWidget);
  });
}
