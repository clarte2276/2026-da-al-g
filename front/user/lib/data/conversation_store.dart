import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'chat_models.dart';

class ConversationStore {
  static final _instance = ConversationStore._();
  static ConversationStore get instance => _instance;
  ConversationStore._();

  final _conversations = <Conversation>[];
  SharedPreferences? _prefs;
  String? _key;

  /// 로그인한 사용자의 대화만 불러온다. 다른 사용자의 기록은 보이지 않는다.
  Future<void> load(String userId) async {
    _prefs = await SharedPreferences.getInstance();
    _key = 'conversations_v2_$userId';
    _conversations.clear();
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
  }

  List<Conversation> get conversations => List.unmodifiable(_conversations);

  void addOrUpdate(Conversation conv) {
    final i = _conversations.indexWhere((c) => c.id == conv.id);
    if (i == -1) {
      _conversations.insert(0, conv);
    } else {
      _conversations[i] = conv;
    }
    _persist();
  }

  void remove(String id) {
    _conversations.removeWhere((c) => c.id == id);
    _persist();
  }

  void _persist() {
    final key = _key;
    if (key == null) return;
    _prefs?.setString(
      key,
      jsonEncode(_conversations.map((c) => c.toJson()).toList()),
    );
  }
}
