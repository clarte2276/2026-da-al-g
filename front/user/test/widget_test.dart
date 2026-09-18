import 'package:flutter_test/flutter_test.dart';

import 'package:user/app.dart';

void main() {
  testWidgets('login screen is shown', (WidgetTester tester) async {
    await tester.pumpWidget(const MyApp());

    expect(find.text('Da-Al-G AI'), findsOneWidget);
    expect(find.text('로그인'), findsOneWidget);
    expect(find.text('개발 테스트 계정: test / test'), findsOneWidget);
  });
}
