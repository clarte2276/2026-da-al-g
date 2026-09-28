import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:user/services/ai_api_client.dart';

AiApiClient _clientReturning(String body) => AiApiClient(
  baseUrl: 'http://test',
  httpClient: MockClient.streaming(
    (request, _) async => http.StreamedResponse(
      Stream.value(utf8.encode(body)),
      200,
    ),
  ),
);

void main() {
  test('parses status, deltas and final done event', () async {
    final body = [
      {'type': 'status', 'text': '규정을 찾는 중'},
      {'type': 'delta', 'text': '관제에 '},
      {'type': 'delta', 'text': '보고'},
      {'type': 'done', 'answer': '관제에 보고합니다.', 'mode': 'rag', 'evidence': []},
    ].map(jsonEncode).join('\n');

    final events = await _clientReturning(body).askStream('q').toList();

    expect(events.map((e) => e.type), [
      AiChatEventType.status,
      AiChatEventType.delta,
      AiChatEventType.delta,
      AiChatEventType.done,
    ]);
    expect(events[1].text + events[2].text, '관제에 보고');
    expect(events.last.response!.answer, '관제에 보고합니다.');
  });

  test('stream cut before done is an error', () async {
    final body = jsonEncode({'type': 'delta', 'text': '관제에 '});

    expect(
      _clientReturning(body).askStream('q').toList(),
      throwsA(isA<AiApiException>()),
    );
  });
}
