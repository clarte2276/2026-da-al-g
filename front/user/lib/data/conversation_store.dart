import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'chat_models.dart';
import '../services/ai_api_client.dart';

class ConversationStore {
  static final _instance = ConversationStore._();
  static ConversationStore get instance => _instance;
  ConversationStore._();

  final _conversations = <Conversation>[];
  SharedPreferences? _prefs;
  String? _key;
  String? _pendingKey;
  final Map<String, String> _pending = {};
  Future<void>? _syncing;

  /// 로그인한 사용자의 대화만 불러온다. 다른 사용자의 기록은 보이지 않는다.
  Future<void> load(String userId) async {
    _prefs = await SharedPreferences.getInstance();
    _key = 'conversations_v2_$userId';
    _pendingKey = 'conversation_pending_$userId';
    _conversations.clear();
    _pending.clear();
    final pendingRaw = _prefs!.getString(_pendingKey!);
    if (pendingRaw != null) {
      _pending.addAll((jsonDecode(pendingRaw) as Map<String, dynamic>).cast<String, String>());
    }
    // 소유자를 알 수 없는 이전 공용 기록은 폐기.
    await _prefs!.remove('conversations_v1');
    final raw = _prefs!.getString(_key!);
    if (raw != null) {
      try {
        final list = jsonDecode(raw) as List;
        _conversations.addAll(
          list.map((e) => Conversation.fromJson(e as Map<String, dynamic>)),
        );
      } catch (_) {}
    }
  }

  /// 로그아웃: 메모리에서만 비운다. 저장된 기록은 같은 사용자가 다시 로그인하면 복원된다.
  void clear() {
    _conversations.clear();
    _key = null;
    _pendingKey = null;
    _pending.clear();
  }

  List<Conversation> get conversations => List.unmodifiable(_conversations);

  void addOrUpdate(Conversation conv) {
    final i = _conversations.indexWhere((c) => c.id == conv.id);
    if (i == -1) {
      _conversations.insert(0, conv);
    } else {
      _conversations[i] = conv;
    }
    _pending[conv.id] = 'save';
    _persist();
  }

  void remove(String id) {
    _conversations.removeWhere((c) => c.id == id);
    _pending[id] = 'delete';
    _persist();
  }

  Future<void> sync() => _syncing ??= _sync().whenComplete(() => _syncing = null);

  Future<void> _sync() async {
    if (_key == null) return;
    final client = AiApiClient();
    try {
      while (true) {
        for (final entry in _pending.entries.toList()) {
          if (_key == null) return;
          final item = _conversations.where((c) => c.id == entry.key).firstOrNull;
          try {
            if (entry.value == 'delete') {
              await client.deleteConversation(entry.key);
            } else if (item != null) {
              await client.saveConversation(item.toJson());
            }
            if (_pending[entry.key] == entry.value &&
                (entry.value == 'delete' || identical(_conversations.where((c) => c.id == entry.key).firstOrNull, item))) {
              _pending.remove(entry.key);
            }
          } on AiApiException catch (e) {
            if (e.statusCode != 410) rethrow;
            _pending.remove(entry.key);
            _conversations.removeWhere((c) => c.id == entry.key);
          }
        }
        final remote = await client.fetchConversations();
        if (_key == null) return;
        if (_pending.isNotEmpty) continue;
        _conversations
          ..clear()
          ..addAll(remote.map(Conversation.fromJson));
        await _writeLocal();
        break;
      }
    } finally {
      client.close();
    }
  }

  void _persist() {
    _writeLocal();
    sync().catchError((_) {});
  }

  Future<void> _writeLocal() async {
    final key = _key;
    if (key == null) return;
    await _prefs?.setString(
      key,
      jsonEncode(_conversations.map((c) => c.toJson()).toList()),
    );
    if (_pendingKey != null) await _prefs?.setString(_pendingKey!, jsonEncode(_pending));
  }
}
