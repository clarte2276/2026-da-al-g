import 'package:flutter_test/flutter_test.dart';
import 'package:user/data/chat_models.dart';

void main() {
  test('reads legacy single source and round-trips multiple sources', () {
    final src = {'regulation': 'R', 'chapter': 'C', 'version': 'V'};
    final legacy = ChatMsg.fromJson({'isUser': false, 'text': 'a', 'source': src});
    expect(legacy.sources.single.regulation, 'R');

    final multi = ChatMsg(isUser: false, text: 'b', sources: [
      ChatSource.fromJson(src),
      ChatSource.fromJson({...src, 'retriever': '그래프 1 hop'}),
    ]);
    final back = ChatMsg.fromJson(multi.toJson());
    expect(back.sources.map((s) => s.isRelated), [false, true]);
    expect(ChatMsg.fromJson({'isUser': true, 'text': 'q'}).sources, isEmpty);
  });
}
