import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:user/services/ai_api_client.dart';

void main() {
  test('page count waits while the server is still converting (202)', () async {
    var calls = 0;
    final client = AiApiClient(
      baseUrl: 'http://test',
      httpClient: MockClient((request) async {
        expect(request.url.path, '/api/documents/d1/pages');
        return ++calls < 3
            ? http.Response('{"detail":"converting"}', 202)
            : http.Response('{"page_count": 12, "version_id": "v1"}', 200);
      }),
    );

    expect(await client.fetchPageCount('d1'), 12);
    expect(calls, 3);
  });

  test('conversion failure surfaces as an error', () async {
    final client = AiApiClient(
      baseUrl: 'http://test',
      httpClient: MockClient((_) async => http.Response.bytes(utf8.encode('{"detail":"변환 실패"}'), 422)),
    );

    expect(client.fetchPageCount('d1'), throwsA(isA<AiApiException>()));
  });
}
