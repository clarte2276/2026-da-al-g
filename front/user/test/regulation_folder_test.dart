import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:user/screens/regulation_library_screen.dart';

void main() {
  testWidgets('regulations are browsed by the data_pdf folder tree', (tester) async {
    const docs = [
      {'id': '1', 'title': '[별표 1] 운전명령서', 'folder': '규정/관제업무/관제업무내규'},
      {'id': '2', 'title': '관제업무내규', 'folder': '규정/관제업무/관제업무내규'},
      {'id': '3', 'title': '복지후생규정', 'folder': '규정/복무.보수/복지후생규정'},
      {'id': '4', 'title': '길라잡이-1', 'folder': '길라잡이/연결 규정_무'},
      {'id': '5', 'title': '루트 문서', 'folder': ''},
    ];
    await tester.pumpWidget(
      const MaterialApp(home: RegulationFolderView(docs: docs, path: [])),
    );

    // 최상위: 폴더 두 개 + 루트 문서, 하위 문서는 안 보인다.
    expect(find.text('규정'), findsOneWidget);
    expect(find.text('길라잡이'), findsOneWidget);
    expect(find.text('루트 문서'), findsOneWidget);
    expect(find.text('관제업무내규'), findsNothing);

    await tester.tap(find.text('규정'));
    await tester.pumpAndSettle();
    expect(find.text('관제업무'), findsOneWidget);
    expect(find.text('복무.보수'), findsOneWidget);

    await tester.tap(find.text('관제업무'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('관제업무내규'));
    await tester.pumpAndSettle();

    // 본 규정이 [별표]보다 먼저.
    final main = tester.getTopLeft(find.text('관제업무내규').last).dy;
    final annex = tester.getTopLeft(find.text('[별표 1] 운전명령서')).dy;
    expect(main, lessThan(annex));
    expect(find.text('규정 › 관제업무 › 관제업무내규'), findsOneWidget);
  });
}
