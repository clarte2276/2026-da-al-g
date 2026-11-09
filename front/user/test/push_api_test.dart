import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:user/services/ai_api_client.dart';

void main() {
  test('registers and unregisters push tokens with bearer auth', () async {
    final requests = <http.Request>[];
    final client = AiApiClient(
      baseUrl: 'https://example.test',
      httpClient: MockClient((request) async {
        requests.add(request);
        return http.Response('{"status":"ok"}', 200);
      }),
    );
    addTearDown(client.close);

    await client.registerPushToken('fcm-token', 'access-token');
    await client.unregisterPushToken('fcm-token', 'access-token');

    expect(requests.map((request) => request.method), ['POST', 'DELETE']);
    for (final request in requests) {
      expect(request.url.path, '/api/push/token');
      expect(request.headers['authorization'], 'Bearer access-token');
      expect(jsonDecode(request.body), {'token': 'fcm-token'});
    }
  });
}
