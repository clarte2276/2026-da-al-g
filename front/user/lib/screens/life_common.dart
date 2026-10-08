import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../core/colors.dart';
import '../services/auth_session.dart';

/// 부가기능 화면들이 공유하는 작은 도우미.
bool get isAdmin => AuthSession.current?.user.isAdmin ?? false;

typedef Json = Map<String, dynamic>;

Scaffold lifeScaffold(String title, Widget body, {Widget? fab, List<Widget>? actions, PreferredSizeWidget? bottom}) =>
    Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(title: Text(title), actions: actions, bottom: bottom),
      floatingActionButton: fab,
      body: body,
    );

/// FutureBuilder + 당겨서 새로고침 + 빈/오류 상태.
class AsyncList extends StatelessWidget {
  const AsyncList({super.key, required this.future, required this.item, required this.onRefresh, this.empty = '아직 내용이 없습니다'});
  final Future<List<Json>> future;
  final Widget Function(Json) item;
  final Future<void> Function() onRefresh;
  final String empty;

  @override
  Widget build(BuildContext context) => FutureBuilder<List<Json>>(
        future: future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
          final Widget child;
          if (snap.hasError) {
            child = _Message('불러오지 못했습니다\n${snap.error}');
          } else if (snap.data!.isEmpty) {
            child = _Message(empty);
          } else {
            child = ListView.separated(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 96),
              itemCount: snap.data!.length,
              separatorBuilder: (_, _) => const SizedBox(height: 10),
              itemBuilder: (_, i) => item(snap.data![i]),
            );
          }
          return RefreshIndicator(onRefresh: onRefresh, child: child);
        },
      );
}

class _Message extends StatelessWidget {
  const _Message(this.text);
  final String text;

  @override
  Widget build(BuildContext context) => ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        children: [
          Padding(
            padding: const EdgeInsets.all(48),
            child: Text(text, textAlign: TextAlign.center, style: TextStyle(color: AppColors.ghostText)),
          ),
        ],
      );
}

/// 입력 칸 여러 개를 받는 대화상자. 취소하면 null.
Future<List<String>?> promptFields(BuildContext context, String title, List<String> labels, {List<String>? initial, int maxLines = 1}) {
  final controllers = [
    for (var i = 0; i < labels.length; i++) TextEditingController(text: initial != null && i < initial.length ? initial[i] : ''),
  ];
  return showDialog<List<String>>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text(title),
      content: SingleChildScrollView(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          for (var i = 0; i < labels.length; i++)
            TextField(
              controller: controllers[i],
              autofocus: i == 0,
              minLines: 1,
              maxLines: i == labels.length - 1 ? maxLines : 1,
              decoration: InputDecoration(labelText: labels[i]),
            ),
        ]),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('취소')),
        FilledButton(onPressed: () => Navigator.pop(context, [for (final c in controllers) c.text.trim()]), child: const Text('확인')),
      ],
    ),
  );
}

/// 작업 실패를 스낵바로 알린다.
Future<bool> runAction(BuildContext context, Future<void> Function() action, {String? done}) async {
  final messenger = ScaffoldMessenger.of(context);
  try {
    await action();
    if (done != null) messenger.showSnackBar(SnackBar(content: Text(done)));
    return true;
  } catch (e) {
    messenger.showSnackBar(SnackBar(content: Text('실패: $e')));
    return false;
  }
}

String shortTime(Object? iso) {
  final t = DateTime.tryParse('${iso ?? ''}')?.toLocal();
  if (t == null) return '';
  String two(int v) => v.toString().padLeft(2, '0');
  return '${t.month}/${t.day} ${two(t.hour)}:${two(t.minute)}';
}

class InfoCard extends StatelessWidget {
  const InfoCard({super.key, required this.title, this.subtitle, this.trailing, this.onTap, this.leading});
  final String title;
  final String? subtitle;
  final Widget? trailing;
  final Widget? leading;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => Material(
        color: AppColors.card,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14), side: BorderSide(color: AppColors.border)),
        child: ListTile(
          onTap: onTap,
          leading: leading,
          title: Text(title, style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.ink)),
          subtitle: subtitle == null ? null : Text(subtitle!, style: TextStyle(color: AppColors.secondaryInk)),
          trailing: trailing,
        ),
      );
}

Future<void> openLink(BuildContext context, String url) async {
  final uri = Uri.tryParse(url);
  if (uri == null || !await launchUrl(uri, mode: LaunchMode.externalApplication)) {
    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('링크를 열 수 없습니다')));
  }
}
