import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../services/life_api.dart';
import 'life_common.dart';

/// 익명 의견·버그 제보. 서버는 이름·사번을 저장하지 않는다.
class VoiceScreen extends StatefulWidget {
  const VoiceScreen({super.key});
  @override
  State<VoiceScreen> createState() => _VoiceScreenState();
}

class _VoiceScreenState extends State<VoiceScreen> {
  final _api = LifeApi();
  late Future<List<Json>> _future = _load();

  Future<List<Json>> _load() => isAdmin ? _api.fetchAllVoiceThreads() : _api.fetchVoiceThreads();

  Future<void> _reload() async {
    setState(() => _future = _load());
    await _future.catchError((_) => <Json>[]);
  }

  Future<void> _write({String? threadId}) async {
    final v = await promptFields(context, threadId == null ? '익명 제보 (5~1000자)' : '답글', ['내용'], maxLines: 8);
    if (v == null || !mounted || v[0].isEmpty) return;
    final ok = await runAction(
      context,
      () => threadId == null ? _api.createVoiceThread(v[0]) : _api.replyToVoice(threadId, v[0]),
      done: threadId == null ? '익명으로 보냈습니다' : null,
    );
    if (ok) _reload();
  }

  @override
  void dispose() {
    _api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => lifeScaffold(
        isAdmin ? '익명 제보 (전체)' : '익명 제보',
        Column(children: [
          if (!isAdmin)
            Container(
              width: double.infinity,
              color: AppColors.softEvidence,
              padding: const EdgeInsets.all(12),
              child: Text('이름과 사번은 저장되지 않습니다. 내가 쓴 제보와 운영자 답글만 보입니다.',
                  style: TextStyle(color: AppColors.secondaryInk, fontSize: 13)),
            ),
          Expanded(
            child: AsyncList(
              future: _future,
              onRefresh: _reload,
              empty: '보낸 제보가 없습니다',
              item: (t) {
                final replies = (t['replies'] as List? ?? []).cast<Json>();
                return Card(
                  elevation: 0,
                  color: AppColors.card,
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(t['content'] ?? '', style: TextStyle(color: AppColors.ink)),
                      Text(shortTime(t['created_at']), style: TextStyle(color: AppColors.ghostText, fontSize: 12)),
                      for (final r in replies)
                        Container(
                          margin: const EdgeInsets.only(top: 8),
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: r['from_admin'] == true ? AppColors.softEvidence : AppColors.canvas,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Text('${r['from_admin'] == true ? '운영자' : '나'}: ${r['content']}'),
                        ),
                      Align(
                        alignment: Alignment.centerRight,
                        child: TextButton(onPressed: () => _write(threadId: '${t['id']}'), child: const Text('답글')),
                      ),
                    ]),
                  ),
                );
              },
            ),
          ),
        ]),
        fab: isAdmin ? null : FloatingActionButton.extended(onPressed: _write, icon: const Icon(Icons.edit), label: const Text('제보하기')),
      );
}
