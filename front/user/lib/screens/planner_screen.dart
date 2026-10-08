import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../core/local_life_store.dart';
import 'life_common.dart';

/// 할 일 · 일정 · 빠른 메모 (기기 저장).
class PlannerScreen extends StatefulWidget {
  const PlannerScreen({super.key});
  @override
  State<PlannerScreen> createState() => _PlannerScreenState();
}

class _PlannerScreenState extends State<PlannerScreen> {
  Planner? _planner;
  final _memo = TextEditingController();

  @override
  void initState() {
    super.initState();
    Planner.load().then((p) => setState(() {
          _planner = p;
          _memo.text = p.memo;
        }));
  }

  @override
  void dispose() {
    _memo.dispose();
    super.dispose();
  }

  Future<void> _update(void Function(Planner) change) async {
    setState(() => change(_planner!));
    await _planner!.save();
  }

  Future<void> _addTodo() async {
    final v = await promptFields(context, '할 일', ['내용']);
    if (v != null && v[0].isNotEmpty) _update((p) => p.todos.add({'text': v[0], 'done': false}));
  }

  Future<void> _addEvent() async {
    final date = await showDatePicker(
      context: context,
      firstDate: DateTime.now().subtract(const Duration(days: 365)),
      lastDate: DateTime.now().add(const Duration(days: 730)),
    );
    if (date == null || !mounted) return;
    final v = await promptFields(context, '${date.month}월 ${date.day}일 일정', ['내용']);
    final key = '${monthKey(date)}-${date.day.toString().padLeft(2, '0')}';
    if (v != null && v[0].isNotEmpty) _update((p) => p.addEvent(key, v[0]));
  }

  Widget _section(String title, VoidCallback? onAdd) => Padding(
        padding: const EdgeInsets.only(top: 16, bottom: 4),
        child: Row(children: [
          Expanded(child: Text(title, style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800, color: AppColors.ink))),
          if (onAdd != null) IconButton(onPressed: onAdd, icon: const Icon(Icons.add_circle_outline)),
        ]),
      );

  @override
  Widget build(BuildContext context) {
    final p = _planner;
    if (p == null) return lifeScaffold('일정관리', const Center(child: CircularProgressIndicator()));
    final done = p.todos.where((t) => t['done'] == true).length;
    final upcoming = p.upcoming(DateTime.now());
    return lifeScaffold(
      '일정관리',
      ListView(padding: const EdgeInsets.all(16), children: [
        _section('오늘의 할 일 ($done/${p.todos.length})', _addTodo),
        if (p.todos.isNotEmpty) LinearProgressIndicator(value: done / p.todos.length, color: AppColors.line6),
        for (var i = 0; i < p.todos.length; i++)
          CheckboxListTile(
            contentPadding: EdgeInsets.zero,
            value: p.todos[i]['done'] == true,
            title: Text('${p.todos[i]['text']}'),
            onChanged: (v) => _update((p) => p.todos[i]['done'] = v),
            secondary: IconButton(icon: const Icon(Icons.close), onPressed: () => _update((p) => p.todos.removeAt(i))),
          ),
        _section('다가오는 일정', _addEvent),
        if (upcoming.isEmpty) Text('예정된 일정이 없습니다', style: TextStyle(color: AppColors.ghostText)),
        for (final e in upcoming)
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: Text('${e['date']}'.substring(5).replaceFirst('-', '/'), style: const TextStyle(fontWeight: FontWeight.w800)),
            title: Text('${e['title']}'),
            trailing: IconButton(icon: const Icon(Icons.close), onPressed: () => _update((p) => p.events.remove(e))),
          ),
        _section('빠른 메모', null),
        TextField(
          controller: _memo,
          minLines: 4,
          maxLines: 12,
          decoration: const InputDecoration(border: OutlineInputBorder(), hintText: '자유롭게 적어두세요 (자동 저장)'),
          onChanged: (v) => _update((p) => p.memo = v),
        ),
      ]),
    );
  }
}
