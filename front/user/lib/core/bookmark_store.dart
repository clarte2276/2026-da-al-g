import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../data/chat_models.dart';
import '../services/auth_session.dart';
import '../services/ai_api_client.dart';

/// 보관함(북마크) 저장소 — 사용자별로 SharedPreferences 에 저장.
class BookmarkStore extends ChangeNotifier {
  BookmarkStore._();
  static final BookmarkStore instance = BookmarkStore._();

  final List<ChatSource> _items = [];
  String? _loadedKey;
  bool _loading = false;
  final Map<String, Map<String, dynamic>> _pending = {};
  Future<void>? _syncing;

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
      _pending.clear();
      final pending = prefs.getString('${_storageKey}_pending');
      if (pending != null) {
        _pending.addAll((jsonDecode(pending) as Map<String, dynamic>).map(
          (k, v) => MapEntry(k, v as Map<String, dynamic>),
        ));
      }
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
      _pending[_key(s)] = {'action': 'delete', 'data': s.toJson()};
      _save();
      notifyListeners();
      return false;
    }
    _items.insert(0, s);
    _pending[_key(s)] = {'action': 'save', 'data': s.toJson()};
    _save();
    notifyListeners();
    return true;
  }

  void remove(ChatSource s) {
    _removeLocal(s);
    _pending[_key(s)] = {'action': 'delete', 'data': s.toJson()};
    _save();
    notifyListeners();
  }

  void _removeLocal(ChatSource s) {
    _items.removeWhere((e) => _key(e) == _key(s));
  }

  // Keep a local copy for offline use; pending writes retry on the next sign-in.
  Future<void> _save() async {
    await _saveLocal();
    sync().catchError((_) {});
  }

  Future<void> sync() => _syncing ??= _sync().whenComplete(() => _syncing = null);

  Future<void> _sync() async {
    final client = AiApiClient();
    try {
      while (true) {
        for (final entry in _pending.entries.toList()) {
          final item = entry.value['data'] as Map<String, dynamic>;
          try {
            if (entry.value['action'] == 'delete') {
              await client.deleteBookmark(item);
            } else {
              await client.saveBookmark(item);
            }
            if (identical(_pending[entry.key], entry.value)) _pending.remove(entry.key);
          } on AiApiException catch (e) {
            if (e.statusCode != 410) rethrow;
            _pending.remove(entry.key);
            _items.removeWhere((s) => _key(s) == entry.key);
          }
        }
        final remote = await client.fetchBookmarks();
        if (_pending.isNotEmpty) continue;
        _items
          ..clear()
          ..addAll(remote.map(ChatSource.fromJson));
        await _saveLocal();
        notifyListeners();
        break;
      }
    } finally {
      client.close();
    }
  }

  Future<void> _saveLocal() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _storageKey,
      jsonEncode(_items.map((e) => e.toJson()).toList()),
    );
    await prefs.setString('${_storageKey}_pending', jsonEncode(_pending));
  }
}
