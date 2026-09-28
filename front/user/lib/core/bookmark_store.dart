import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../data/mock_conversations.dart';
import '../services/auth_session.dart';

/// 보관함(북마크) 저장소 — 사용자별로 SharedPreferences 에 저장.
class BookmarkStore extends ChangeNotifier {
  BookmarkStore._();
  static final BookmarkStore instance = BookmarkStore._();

  final List<ChatSource> _items = [];
  String? _loadedKey;
  bool _loading = false;

  List<ChatSource> get items => List.unmodifiable(_items);

  String get _storageKey =>
      'bookmarks_${AuthSession.current?.user.id ?? 'guest'}';

  String _key(ChatSource s) => '${s.regulation}|${s.chapter}';

  bool isBookmarked(ChatSource s) => _items.any((e) => _key(e) == _key(s));

  /// 화면 진입 시 호출. 로그인 사용자가 바뀌었으면 다시 읽는다.
  Future<void> ensureLoaded() async {
    if (_loadedKey == _storageKey || _loading) return;
    await refresh();
  }

  Future<void> refresh() async {
    _loading = true;
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_storageKey);
      _items.clear();
      if (raw != null) {
        _items.addAll(
          (jsonDecode(raw) as List)
              .whereType<Map<String, dynamic>>()
              .map(ChatSource.fromJson),
        );
      }
      _loadedKey = _storageKey;
      notifyListeners();
    } catch (_) {
      // 손상된 캐시: 빈 상태 유지
    } finally {
      _loading = false;
    }
  }

  /// 저장돼 있으면 해제, 없으면 추가. 추가됐으면 true.
  bool toggle(ChatSource s) {
    final exists = isBookmarked(s);
    if (exists) {
      _removeLocal(s);
      _save();
      notifyListeners();
      return false;
    }
    _items.insert(0, s);
    _save();
    notifyListeners();
    return true;
  }

  void remove(ChatSource s) {
    _removeLocal(s);
    _save();
    notifyListeners();
  }

  void _removeLocal(ChatSource s) {
    _items.removeWhere((e) => _key(e) == _key(s));
  }

  // ponytail: 백엔드에 북마크 API가 없어 기기 로컬에만 저장. 서버 API가 생기면 여기서 동기화.
  Future<void> _save() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _storageKey,
      jsonEncode(_items.map((e) => e.toJson()).toList()),
    );
  }
}
