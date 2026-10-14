import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:user/app_shell.dart';
import 'package:user/core/duty_data.dart';
import 'package:user/data/chat_models.dart';
import 'package:user/data/conversation_store.dart';
import 'package:user/screens/chat_room_screen.dart';
import 'package:user/screens/duty_board_screen.dart';
import 'package:user/screens/login_screen.dart';
import 'package:user/screens/my_page_screen.dart';
import 'package:user/widgets/turn_sheet.dart';

/// 기기 글자 크기를 최대(2배)로 키워도 폰 화면에서 레이아웃이 넘치지 않는지 확인한다.
/// 넘치면 RenderFlex overflow 오류로 테스트가 실패한다.
Future<void> pumpScaled(WidgetTester tester, Widget home) async {
  tester.view.physicalSize = const Size(390 * 3, 844 * 3);
  tester.view.devicePixelRatio = 3;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    MaterialApp(
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(context).copyWith(textScaler: const TextScaler.linear(2)),
        child: child!,
      ),
      home: home,
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  setUp(() {
    final now = DateTime.now();
    final month = '${now.year}-${now.month.toString().padLeft(2, '0')}';
    final fixture = File('assets/data/duty_2026_06.json').readAsStringSync();
    SharedPreferences.setMockInitialValues({'duty_month_$month': fixture});
    DutyRepository.instance.invalidate(month);
  });

  testWidgets('tabs survive 2x text', (tester) async {
    await tester.runAsync(() async {
      await ConversationStore.instance.load('scale');
      await DutyRepository.instance.load();
    });
    await pumpScaled(tester, const AppShell());

    for (final icon in [
      Icons.calendar_month_outlined,
      Icons.chat_bubble_outline_rounded,
      Icons.settings_outlined,
    ]) {
      await tester.tap(find.byIcon(icon));
      await tester.pumpAndSettle();
    }
  });

  testWidgets('duty calendar and 행로표 sheet survive 2x text', (tester) async {
    final data = (await tester.runAsync(() => DutyRepository.instance.load()))!;
    await pumpScaled(tester, const DutyBoardScreen());
    expect(find.text('근무 요약'), findsOneWidget);

    final context = tester.element(find.byType(DutyBoardScreen));
    unawaited(showDaySheet(
      context,
      data: data,
      driver: data.drivers.first,
      date: data.dates.first,
      subtitle: '6/1',
    ));
    await tester.pumpAndSettle();
    expect(find.text('교번 63'), findsOneWidget);
    expect(find.text('평평'), findsOneWidget);
    expect(find.text('출근'), findsOneWidget);
    Navigator.of(context).pop();
    await tester.pumpAndSettle();
  });

  testWidgets('chat room with sources survives 2x text', (tester) async {
    await pumpScaled(
      tester,
      ChatRoomScreen(
        conversation: Conversation(
          id: 's',
          title: '출입문 고장 시 승객 안내',
          createdAt: DateTime.now(),
          messages: [
            ChatMsg(isUser: true, text: '출입문 고장 시 승객 안내'),
            ChatMsg(
              isUser: false,
              text: '답변 **굵게**',
              sources: [
                ChatSource(regulation: '운전취급규정', chapter: '제1조', version: '', excerpt: '발췌'),
                ChatSource(regulation: '안전관리규정', chapter: '제2조', version: '', retriever: '그래프 1 hop'),
              ],
            ),
          ],
        ),
      ),
    );
  });

  testWidgets('login and my page survive 2x text', (tester) async {
    await pumpScaled(tester, const LoginScreen());
    await pumpScaled(tester, const MyPageScreen());
  });
}
