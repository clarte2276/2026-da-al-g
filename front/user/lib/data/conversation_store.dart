import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'mock_conversations.dart';

class ConversationStore {
  static final _instance = ConversationStore._();
  static ConversationStore get instance => _instance;
  ConversationStore._();

  final _conversations = <Conversation>[];
  SharedPreferences? _prefs;
  static const _key = 'conversations_v1';

  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
    final raw = _prefs!.getString(_key);
    if (raw != null) {
      try {
        final list = jsonDecode(raw) as List;
        _conversations.addAll(
          list.map((e) => Conversation.fromJson(e as Map<String, dynamic>)),
        );
        return;
      } catch (_) {}
    }
    // ponytail: seed with mock data on first run
    _conversations.addAll(mockConversations);
    _persist();
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
    _prefs?.setString(
      _key,
      jsonEncode(_conversations.map((c) => c.toJson()).toList()),
    );
  }
}
