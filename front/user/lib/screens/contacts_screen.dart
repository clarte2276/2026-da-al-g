import 'package:flutter/material.dart';
import '../services/life_api.dart';
import 'life_common.dart';

/// 비상 연락처. 번호는 관리자가 등록한 것만 보여준다.
class ContactsScreen extends StatefulWidget {
  const ContactsScreen({super.key});
  @override
  State<ContactsScreen> createState() => _ContactsScreenState();
}

class _ContactsScreenState extends State<ContactsScreen> {
  final _api = LifeApi();
  late Future<List<Json>> _future = _api.fetchContacts();

  Future<void> _reload() async {
    setState(() => _future = _api.fetchContacts());
    await _future.catchError((_) => <Json>[]);
  }

  Future<void> _edit(List<Json> current, {int? index}) async {
    final old = index == null ? null : current[index];
    final v = await promptFields(context, old == null ? '연락처 추가' : '연락처 수정', ['구분 (예: 관제)', '이름', '전화번호'],
        initial: old == null ? null : ['${old['group'] ?? ''}', '${old['name'] ?? ''}', '${old['phone'] ?? ''}']);
    if (v == null || !mounted) return;
    final next = [...current];
    final entry = {'group': v[0], 'name': v[1], 'phone': v[2]};
    if (index == null) {
      if (v[1].isEmpty || v[2].isEmpty) return;
      next.add(entry);
    } else if (v[1].isEmpty && v[2].isEmpty) {
      next.removeAt(index); // 이름과 번호를 비우면 삭제
    } else {
      next[index] = entry;
    }
    if (await runAction(context, () => _api.updateContacts(next))) _reload();
  }

  @override
  void dispose() {
    _api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<List<Json>>(
        future: _future,
        builder: (context, snap) => lifeScaffold(
          '비상 연락처',
          AsyncList(
            future: _future,
            onRefresh: _reload,
            empty: isAdmin ? '+ 버튼으로 연락처를 등록하세요' : '등록된 연락처가 없습니다',
            item: (c) => InfoCard(
              leading: const Icon(Icons.phone),
              title: '${c['name']}',
              subtitle: '${c['group'] ?? ''} · ${c['phone']}',
              onTap: () => openLink(context, 'tel:${'${c['phone']}'.replaceAll(RegExp(r'[^0-9+]'), '')}'),
              trailing: isAdmin
                  ? IconButton(icon: const Icon(Icons.edit), onPressed: () => _edit(snap.data ?? [], index: snap.data!.indexOf(c)))
                  : null,
            ),
          ),
          fab: isAdmin && snap.hasData ? FloatingActionButton(onPressed: () => _edit(snap.data!), child: const Icon(Icons.add)) : null,
        ),
      );
}
