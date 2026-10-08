import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:user/main.dart';
import 'package:user/screens/inquiry_screen.dart';
import 'package:user/screens/password_setup_screen.dart';
import 'package:user/services/ai_api_client.dart';
import 'package:user/services/auth_session.dart';

AuthResponse _session({bool mustChangePassword = false}) => AuthResponse(
  accessToken: 'token',
  tokenType: 'bearer',
  user: AuthUser(
    id: 'u1',
    name: '홍길동',
    employeeId: '1234',
    email: '',
    line: '6호선',
    mustChangePassword: mustChangePassword,
  ),
);

void main() {
  tearDown(() => AuthSession.current = null);

  test('must_change_password defaults to false and parses true', () {
    final legacy = AuthUser.fromJson({'id': 'u1'});
    final required = AuthUser.fromJson({
      'id': 'u1',
      'must_change_password': true,
    });

    expect(legacy.mustChangePassword, isFalse);
    expect(required.mustChangePassword, isTrue);
  });

  testWidgets('forces password setup only when the session requires it', (
    tester,
  ) async {
    AuthSession.current = _session(mustChangePassword: true);
    await tester.pumpWidget(
      const MaterialApp(
        home: AuthSessionGate(child: Scaffold(body: Text('app content'))),
      ),
    );
    expect(find.byType(PasswordSetupScreen), findsOneWidget);
    expect(find.text('app content'), findsNothing);

    AuthSession.current = _session();
    await tester.pump();
    expect(find.byType(PasswordSetupScreen), findsNothing);
    expect(find.text('app content'), findsOneWidget);
  });

  testWidgets('password-change-required API errors force setup', (
    tester,
  ) async {
    AuthSession.current = _session();
    await tester.pumpWidget(
      const MaterialApp(
        home: AuthSessionGate(child: Scaffold(body: Text('app content'))),
      ),
    );

    AiApiException('password_change_required', statusCode: 403);
    await tester.pump();

    expect(find.byType(PasswordSetupScreen), findsOneWidget);
    expect(AuthSession.current?.user.mustChangePassword, isTrue);
  });

  testWidgets('renders inquiry items from the API client', (tester) async {
    AuthSession.current = null;
    final client = MockClient((request) async {
      expect(request.url.path, '/api/me/inquiries');
      return http.Response(
        jsonEncode([
          {
            'id': 'inq-1',
            'user_id': 'u1',
            'kind': 'feedback',
            'title': '답변 피드백',
            'body': '설명이 조금 부족했어요.',
            'rating': 'down',
            'question': '운행 중 안내 방법은?',
            'answer': '안내 방송을 진행합니다.',
            'evidence': [],
            'created_at': '2026-10-08T10:00:00Z',
            'replies': [
              {
                'id': 'reply-1',
                'from_admin': true,
                'body': '확인하겠습니다.',
                'created_at': '2026-10-08T11:00:00Z',
              },
            ],
          },
        ]),
        200,
        headers: {'content-type': 'application/json'},
      );
    });
    final api = AiApiClient(
      httpClient: client,
      baseUrl: 'https://example.test',
    );

    await tester.pumpWidget(MaterialApp(home: InquiryScreen(client: api)));
    await tester.pumpAndSettle();

    expect(find.text('답변 피드백'), findsNWidgets(2));
    expect(find.text('답변 완료'), findsOneWidget);
  });
}
