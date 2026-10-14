import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../core/duty_data.dart';
import '../core/personal_store.dart';
import '../services/ai_api_client.dart';
import '../services/auth_session.dart';
import '../services/crew_api.dart';
import 'dia_image_viewer.dart';

/// 행로표(교번 상세)를 바텀시트로 연다. [subtitle]은 날짜·기관사 등 맥락 한 줄.
Future<void> showTurnSheet(
  BuildContext context, {
  required TurnDetail turn,
  bool isDummy = false,
  String? subtitle,
}) {
  return showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: AppColors.card,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (_) => DraggableScrollableSheet(
      expand: false,
      initialChildSize: turn.diaImage?.isNotEmpty == true
          ? 0.75
          : (turn.segments.isEmpty || isDummy ? 0.5 : 0.75),
      maxChildSize: 0.95,
      builder: (context, controller) =>
          TurnSheet(turn: turn, isDummy: isDummy, subtitle: subtitle, controller: controller),
    ),
  );
}

/// 달력에서 고른 하루: 행로표(있으면) 또는 근무 안내 + 메모·교번 변경. 바꾸면 그 자리에서 다시 그린다.
Future<void> showDaySheet(
  BuildContext context, {
  required DutyMonth data,
  required Driver driver,
  required String date,
  required String subtitle,
}) {
  return showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: AppColors.card,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (_) => DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.75,
      maxChildSize: 0.95,
      builder: (context, controller) => ListenableBuilder(
        listenable: PersonalStore.instance,
        builder: (context, _) {
          final duty = data.dutyOn(driver, date);
          final turn = duty == null ? null : data.turnFor(duty) ?? data.turns[duty.continues];
          final footer = Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              DayPersonalPanel(data: data, driver: driver, date: date, duty: duty),
            ],
          );
          if (turn == null) {
            return _PlainDaySheet(duty: duty, subtitle: subtitle, controller: controller, footer: footer);
          }
          return TurnSheet(
            turn: turn,
            isDummy: data.turnDetailIsDummy,
            subtitle: duty!.continues != null && duty.turn == null ? '$subtitle · 전날 교번 이어서' : subtitle,
            controller: controller,
            footer: footer,
          );
        },
      ),
    ),
  );
}

/// "765" → "12시간 45분".
String formatMinutes(int? m) {
  if (m == null) return '-';
  if (m < 60) return '$m분';
  return m % 60 == 0 ? '${m ~/ 60}시간' : '${m ~/ 60}시간 ${m % 60}분';
}

class TurnSheet extends StatelessWidget {
  const TurnSheet({super.key, required this.turn, this.isDummy = false, this.subtitle, this.controller, this.footer});
  final TurnDetail turn;
  final bool isDummy;
  final String? subtitle;
  final ScrollController? controller;
  final Widget? footer; // 메모·교번 변경 패널

  @override
  Widget build(BuildContext context) {
    final c = dutyTypeColor(turn.type);
    return SafeArea(
      child: ListView(
        controller: controller,
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
        children: [
          Center(
            child: Container(
              width: 36,
              height: 4,
              decoration: BoxDecoration(color: AppColors.border, borderRadius: BorderRadius.circular(2)),
            ),
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 8,
            runSpacing: 6,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              Text('교번 ${turn.id}', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
              if (turn.dayType != null) _Badge(turn.dayType!, AppColors.line6),
              _Badge(turn.type.label, c),
            ],
          ),
          if (subtitle != null) ...[
            const SizedBox(height: 4),
            Text(subtitle!, style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)),
          ],
          const SizedBox(height: 16),
          if (isDummy)
            const _Notice('교번별 출무 시각·구간은 아직 연결되지 않았습니다.')
          else ...[
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _Fact('출근', turn.depart),
                _Fact('퇴근', turn.nextDay ? '${turn.arrive} (익일)' : turn.arrive),
                _Fact('근무시간', formatMinutes(turn.workMinutes)),
                _Fact('운전', formatMinutes(turn.driveMinutes)),
                _Fact('대기', formatMinutes(turn.standbyMinutes)),
              ],
            ),
            if (turn.route.isNotEmpty) ...[
              const SizedBox(height: 12),
              Row(children: [
                const Icon(Icons.route_rounded, size: 18, color: AppColors.line6),
                const SizedBox(width: 8),
                Expanded(child: Text(turn.route, style: const TextStyle(fontWeight: FontWeight.w700))),
              ]),
            ],
            const SizedBox(height: 18),
            if (turn.segments.isEmpty)
              const _Notice('상세 행로 정보가 없습니다.')
            else
              for (var i = 0; i < turn.segments.length; i++)
                _SegmentRow(seg: turn.segments[i], last: i == turn.segments.length - 1),
          ],
          if (turn.diaImage?.isNotEmpty ?? false) ...[
            const SizedBox(height: 12),
            Material(
              color: AppColors.canvas,
              borderRadius: BorderRadius.circular(12),
              clipBehavior: Clip.antiAlias,
              child: InkWell(
                onTap: () => showDiaImageViewer(context, turn.diaImage!),
                child: DiaImage(
                  path: turn.diaImage!,
                  width: double.infinity,
                  loadingColor: AppColors.line6,
                  errorColor: AppColors.secondaryInk,
                ),
              ),
            ),
          ],
          ?footer,
        ],
      ),
    );
  }
}

class _SegmentRow extends StatelessWidget {
  const _SegmentRow({required this.seg, required this.last});
  final TurnSegment seg;
  final bool last;

  @override
  Widget build(BuildContext context) {
    final isRun = seg.kind == 'run';
    final accent = seg.kind == 'standby' ? AppColors.ghostText : AppColors.line6;
    final dir = switch (seg.dir) { 'up' => '▲ 상선', 'down' => '▼ 하선', _ => null };
    final time = seg.dep == seg.arr ? seg.dep : '${seg.dep}–${seg.arr}';
    final place = seg.from == seg.to ? seg.from : '${seg.from} → ${seg.to}';
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SizedBox(
            width: 20,
            child: Column(children: [
              const SizedBox(height: 4),
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: isRun ? accent : AppColors.card,
                  shape: BoxShape.circle,
                  border: Border.all(color: accent, width: 2),
                ),
              ),
              if (!last) Expanded(child: Container(width: 2, color: AppColors.line6.withValues(alpha: 0.35))),
            ]),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Wrap(
                    spacing: 6,
                    runSpacing: 4,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      Text(time, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
                      if (seg.nextDay) Text('익일', style: TextStyle(fontSize: 12, color: AppColors.secondaryInk)),
                      if (dir != null)
                        Text(dir, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.line6)),
                      if (!isRun) _Badge(seg.kindLabel, accent),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    seg.train.isEmpty ? place : '${seg.train}열차 · $place',
                    style: TextStyle(fontSize: 14, color: AppColors.secondaryInk),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Fact extends StatelessWidget {
  const _Fact(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.canvas,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label, style: TextStyle(fontSize: 12, color: AppColors.secondaryInk)),
          Text(value.isEmpty ? '-' : value, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800)),
        ],
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge(this.text, this.color);
  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(8)),
      child: Text(text, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: color)),
    );
  }
}

class _Notice extends StatelessWidget {
  const _Notice(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: AppColors.softEvidence, borderRadius: BorderRadius.circular(10)),
      child: Text(text, style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)),
    );
  }
}

/// 행로표가 없는 날(비번·휴무·대기 등)의 시트.
class _PlainDaySheet extends StatelessWidget {
  const _PlainDaySheet({required this.duty, required this.subtitle, required this.controller, required this.footer});
  final DayDuty? duty;
  final String subtitle;
  final ScrollController controller;
  final Widget footer;

  @override
  Widget build(BuildContext context) {
    final d = duty;
    final standby = d?.type == DutyType.standby;
    return SafeArea(
      child: ListView(
        controller: controller,
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
        children: [
          Center(
            child: Container(
              width: 36,
              height: 4,
              decoration: BoxDecoration(color: AppColors.border, borderRadius: BorderRadius.circular(2)),
            ),
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 8,
            runSpacing: 6,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              Text(d == null ? '근무 정보 없음' : (standby ? standbyLabel(d) : d.code),
                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
              if (d != null) _Badge(standby ? d.code : d.type.label, dutyTypeColor(d.type)),
            ],
          ),
          const SizedBox(height: 4),
          Text(subtitle, style: TextStyle(fontSize: 13, color: AppColors.secondaryInk)),
          if (standby) ...[
            const SizedBox(height: 16),
            const _Notice('충당여부 및 출근시각 확인'),
          ],
          footer,
        ],
      ),
    );
  }
}

/// 날짜별 메모와 교번 변경 흐름.
class DayPersonalPanel extends StatefulWidget {
  const DayPersonalPanel({
    super.key,
    required this.data,
    required this.driver,
    required this.date,
    required this.duty,
  });
  final DutyMonth data;
  final Driver driver;
  final String date;
  final DayDuty? duty;

  @override
  State<DayPersonalPanel> createState() => _DayPersonalPanelState();
}

class _DayPersonalPanelState extends State<DayPersonalPanel> {
  final _api = CrewApi();
  final _client = AiApiClient();
  List<Map<String, dynamic>> _posts = [];
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _loadPosts();
  }

  @override
  void dispose() {
    _api.close();
    _client.close();
    super.dispose();
  }

  Future<void> _loadPosts() async {
    try {
      final posts = await _api.fetchExchangePosts(mine: true);
      if (mounted) setState(() => _posts = posts);
    } catch (_) {
      // Device-only overrides still work while this API is unavailable.
    }
  }

  Map<String, dynamic>? get _pending =>
      pendingDutySwap(_posts, widget.driver.name, widget.date);

  Future<bool> _requestSwap(_DutyCandidate candidate) async {
    final name = candidate.name;
    final theirCode = candidate.code;
    final myCode =
        widget.driver.days[widget.date]?.code ?? widget.duty?.code ?? '';
    if (name.isEmpty || myCode.isEmpty || theirCode.isEmpty) return false;
    setState(() => _busy = true);
    try {
      await _api.createExchangePost({
        'type': 'direct',
        'target_name': name,
        'dates': [widget.date],
        'requester_dias': [myCode],
        'target_dias': [theirCode],
      });
      await _loadPosts();
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('맞교환 요청을 보냈습니다.')));
      }
      return true;
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('맞교환 요청 실패: $e')));
      }
      return false;
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _cancelPending(Map<String, dynamic> post) async {
    final id = post['id'] as String?;
    if (id == null) return;
    setState(() => _busy = true);
    try {
      await _api.deletePost(id);
      await _loadPosts();
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('맞교환 요청을 취소했습니다.')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('요청 취소 실패: $e')));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<bool> _revertSwap() async {
    final id = widget.duty?.swapPostId;
    if (id == null) return false;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('교번 돌아가기'),
        content: const Text('맞교환한 근무를 원래대로 되돌리는 요청을 보낼까요?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('취소'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('요청'),
          ),
        ],
      ),
    );
    if (confirmed != true) return false;
    setState(() => _busy = true);
    try {
      await _client.revertExchangePost(id);
      await _loadPosts();
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('되돌리기 요청을 보냈습니다.')));
      }
      return true;
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('되돌리기 요청 실패: $e')));
      }
      return false;
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<String?> _prompt(
    BuildContext context,
    String title,
    String initial, {
    int maxLines = 1,
  }) {
    final c = TextEditingController(text: initial);
    return showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: TextField(controller: c, autofocus: true, maxLines: maxLines),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('취소'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, c.text),
            child: const Text('저장'),
          ),
        ],
      ),
    );
  }

  Future<void> _openChangeSheet() => showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: AppColors.card,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (_) => _DutyChangeSheet(
      data: widget.data,
      driver: widget.driver,
      date: widget.date,
      duty: widget.duty,
      pendingPosts: _posts,
      hasPending: _pending != null,
      canRequest: AuthSession.current?.user.name == widget.driver.name,
      onRequestSwap: _requestSwap,
      onRevertSwap: _revertSwap,
    ),
  );

  @override
  Widget build(BuildContext context) {
    final store = PersonalStore.instance;
    final memo = store.memo(widget.driver, widget.date);
    final localOverride = store
        .overrides(widget.driver)
        .containsKey(widget.date);
    final pending = _pending;
    final original = widget.duty?.original;
    final label = TextStyle(
      fontSize: 13,
      fontWeight: FontWeight.w700,
      color: AppColors.secondaryInk,
    );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 8),
        Divider(color: AppColors.border),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: _busy ? null : _openChangeSheet,
          icon: const Icon(Icons.swap_horiz_rounded, size: 18),
          label: const Text('교번 변경'),
        ),
        if (localOverride)
          Text(
            '변경 (원래: ${original == null || original.code.isEmpty ? '-' : original.code})',
            style: const TextStyle(
              fontWeight: FontWeight.w800,
              color: AppColors.line6,
            ),
          ),
        if (widget.duty?.swapPostId != null)
          Text(
            '맞교환 적용됨 (원래: ${original?.code.isNotEmpty == true ? original!.code : '-'})',
            style: const TextStyle(
              fontWeight: FontWeight.w800,
              color: AppColors.line6,
            ),
          ),
        if (pending != null) ...[
          Text(
            pending['requester_name'] == widget.driver.name
                ? '맞교환 요청 대기 중'
                : '내게 온 맞교환 요청 대기 중',
            style: const TextStyle(
              fontWeight: FontWeight.w800,
              color: AppColors.line6,
            ),
          ),
          if (pending['requester_name'] == widget.driver.name)
            TextButton.icon(
              onPressed: _busy ? null : () => _cancelPending(pending),
              icon: const Icon(Icons.close_rounded, size: 16),
              label: const Text('교번 돌아가기'),
            ),
        ],
        const SizedBox(height: 16),
        Text('메모', style: label),
        const SizedBox(height: 4),
        Text(
          memo ?? '메모 없음',
          style: TextStyle(
            color: memo == null ? AppColors.ghostText : AppColors.ink,
          ),
        ),
        TextButton.icon(
          onPressed: () async {
            final text = await _prompt(context, '메모', memo ?? '', maxLines: 4);
            if (text != null) {
              await store.setMemo(widget.driver, widget.date, text);
            }
          },
          icon: const Icon(Icons.edit_note_rounded, size: 18),
          label: Text(memo == null ? '메모 쓰기' : '메모 수정'),
        ),
      ],
    );
  }
}

class _DutyCandidate {
  const _DutyCandidate({
    required this.name,
    required this.code,
    this.standalone = false,
    this.changed = false,
    this.pending = false,
    this.startTime,
    this.endTime,
  });

  final String name;
  final String code;
  final bool standalone;
  final bool changed;
  final bool pending;
  final String? startTime;
  final String? endTime;

  String get label => code == '~'
      ? '비번'
      : code == '휴'
      ? '휴무'
      : code;
}

class _DutyChangeSheet extends StatefulWidget {
  const _DutyChangeSheet({
    required this.data,
    required this.driver,
    required this.date,
    required this.duty,
    required this.pendingPosts,
    required this.hasPending,
    required this.canRequest,
    required this.onRequestSwap,
    required this.onRevertSwap,
  });

  final DutyMonth data;
  final Driver driver;
  final String date;
  final DayDuty? duty;
  final List<Map<String, dynamic>> pendingPosts;
  final bool hasPending;
  final bool canRequest;
  final Future<bool> Function(_DutyCandidate) onRequestSwap;
  final Future<bool> Function() onRevertSwap;

  @override
  State<_DutyChangeSheet> createState() => _DutyChangeSheetState();
}

class _DutyChangeSheetState extends State<_DutyChangeSheet> {
  final _client = AiApiClient();
  String _query = '';
  List<Map<String, dynamic>> _matches = [];
  bool _loading = true;
  bool _loadFailed = false;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _loadMatches();
  }

  @override
  void dispose() {
    _client.close();
    super.dispose();
  }

  Future<void> _loadMatches() async {
    try {
      final matches = await _client.fetchExchangeMatches(date: widget.date);
      if (mounted) setState(() => _matches = matches);
    } catch (_) {
      if (mounted) setState(() => _loadFailed = true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  bool _hasPendingWith(String name) => widget.pendingPosts.any((post) {
    final dates = post['dates'] as List?;
    return post['type'] == 'direct' &&
        post['status'] == 'open' &&
        (dates?.contains(widget.date) ?? false) &&
        ((post['requester_name'] == widget.driver.name &&
                post['target_name'] == name) ||
            (post['target_name'] == widget.driver.name &&
                post['requester_name'] == name));
  });

  List<_DutyCandidate> get _candidates {
    final others = <_DutyCandidate>[];
    for (final match in _matches) {
      final name = match['name'] as String? ?? '';
      final code = match['code'] as String? ?? '';
      if (name.isEmpty ||
          name == widget.driver.name ||
          code.isEmpty ||
          code == '~' ||
          code.startsWith('휴')) {
        continue;
      }
      final localDriver = widget.data.drivers
          .where((driver) => driver.name == name)
          .firstOrNull;
      final localDuty = localDriver?.days[widget.date];
      final turnKey = match['turnKey'] as String?;
      final turn =
          (turnKey == null ? null : widget.data.turns[turnKey]) ??
          (localDuty == null ? null : widget.data.turnFor(localDuty));
      others.add(
        _DutyCandidate(
          name: name,
          code: code,
          changed: match['swapped'] == true,
          pending: _hasPendingWith(name),
          startTime: turn?.depart,
          endTime: turn?.arrive,
        ),
      );
    }
    others.sort((a, b) {
      final codeOrder = _compareDutyCodes(a.code, b.code);
      return codeOrder != 0 ? codeOrder : a.name.compareTo(b.name);
    });
    return [
      const _DutyCandidate(name: '', code: '~', standalone: true),
      const _DutyCandidate(name: '', code: '휴', standalone: true),
      ...others,
    ];
  }

  Future<void> _confirmChange(_DutyCandidate candidate) async {
    if (_busy ||
        candidate.changed ||
        candidate.pending ||
        (!candidate.standalone && (!widget.canRequest || widget.hasPending))) {
      return;
    }
    final myCode =
        widget.driver.days[widget.date]?.code ?? widget.duty?.code ?? '';
    final originalCode =
        widget.duty?.original?.code ??
        widget.driver.days[widget.date]?.code ??
        myCode;
    final message = candidate.standalone
        ? '${_formatDate(widget.date)}\n${widget.driver.name} ${_formatCode(originalCode)} → ${candidate.label}\n변경할까요?'
        : '${_formatDate(widget.date)}\n${widget.driver.name} ${_formatCode(myCode)} ↔ ${candidate.name} ${_formatCode(candidate.code)}\n맞교환 요청을 보낼까요?';
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(candidate.standalone ? '교번 변경 확인' : '맞교환 요청'),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('취소'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(candidate.standalone ? '변경' : '요청'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() => _busy = true);
    try {
      final bool applied;
      if (candidate.standalone) {
        await PersonalStore.instance.setOverride(
          widget.driver,
          widget.date,
          candidate.code,
        );
        applied = true;
      } else {
        applied = await widget.onRequestSwap(candidate);
      }
      if (applied && mounted) Navigator.pop(context);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('교번 변경 실패: $e')));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _confirmReturn() async {
    if (_busy) return;
    final store = PersonalStore.instance;
    final hasLocalOverride = store
        .overrides(widget.driver)
        .containsKey(widget.date);
    if (hasLocalOverride) {
      final previous = store.previousOverride(widget.driver, widget.date);
      final original =
          widget.duty?.original?.code ??
          widget.driver.days[widget.date]?.code ??
          '-';
      final action = await showDialog<String>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('교번 돌아가기'),
          content: Text('${_formatDate(widget.date)}\n어디로 돌아갈까요?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('취소'),
            ),
            if (previous != null)
              TextButton(
                onPressed: () => Navigator.pop(context, 'previous'),
                child: Text('직전 ${_formatCode(previous)}'),
              ),
            if (previous != null)
              FilledButton(
                onPressed: () => Navigator.pop(context, 'original'),
                child: Text('맨 처음 ${_formatCode(original)}'),
              ),
            if (previous == null)
              FilledButton(
                onPressed: () => Navigator.pop(context, 'original'),
                child: const Text('되돌리기'),
              ),
          ],
        ),
      );
      if (action == null || !mounted) return;
      setState(() => _busy = true);
      try {
        if (action == 'previous') {
          await store.undoOverride(widget.driver, widget.date);
        } else {
          await store.setOverride(widget.driver, widget.date, null);
        }
        if (mounted) Navigator.pop(context);
      } finally {
        if (mounted) setState(() => _busy = false);
      }
    } else if (widget.duty?.swapPostId != null) {
      final reverted = await widget.onRevertSwap();
      if (reverted && mounted) Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    final duty = widget.duty;
    final localOverride = PersonalStore.instance
        .overrides(widget.driver)
        .containsKey(widget.date);
    final original =
        duty?.original?.code ??
        widget.driver.days[widget.date]?.code ??
        duty?.code ??
        '-';
    final modified =
        localOverride || duty?.swapPostId != null || duty?.original != null;
    final query = _query.trim().toLowerCase();
    final candidates = _candidates
        .where(
          (candidate) =>
              query.isEmpty ||
              candidate.name.toLowerCase().contains(query) ||
              candidate.code.toLowerCase().contains(query) ||
              candidate.label.toLowerCase().contains(query),
        )
        .toList();
    return SafeArea(
      top: false,
      child: SizedBox(
        height: MediaQuery.of(context).size.height * 0.82,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 10, 20, 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 42,
                  height: 5,
                  decoration: BoxDecoration(
                    color: AppColors.border,
                    borderRadius: BorderRadius.circular(3),
                  ),
                ),
              ),
              const SizedBox(height: 14),
              const Text(
                '교번 변경',
                style: TextStyle(fontSize: 23, fontWeight: FontWeight.w900),
              ),
              const SizedBox(height: 14),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 13,
                ),
                decoration: BoxDecoration(
                  color: AppColors.canvas,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _formatDate(widget.date),
                          style: const TextStyle(
                            fontWeight: FontWeight.w900,
                            fontSize: 16,
                          ),
                        ),
                        const SizedBox(height: 5),
                        Text(
                          '원래 ${_formatCode(original)}',
                          style: TextStyle(
                            color: AppColors.secondaryInk,
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ],
                    ),
                    Container(
                      constraints: const BoxConstraints(minWidth: 66),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 8,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.line6.withValues(alpha: 0.14),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Column(
                        children: [
                          Text(
                            '현재',
                            style: TextStyle(
                              color: AppColors.line6,
                              fontSize: 9,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                          Text(
                            _formatCode(duty?.code ?? '-'),
                            style: const TextStyle(
                              color: AppColors.line6,
                              fontSize: 17,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              if (modified) ...[
                const SizedBox(height: 10),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: _busy ? null : _confirmReturn,
                    icon: const Icon(Icons.undo_rounded, size: 16),
                    label: const Text('교번 돌아가기'),
                  ),
                ),
              ],
              const SizedBox(height: 8),
              TextField(
                enabled: !_busy,
                onChanged: (value) => setState(() => _query = value),
                decoration: InputDecoration(
                  hintText: '이름 또는 DIA 검색',
                  prefixIcon: const Icon(Icons.search_rounded),
                  filled: true,
                  fillColor: AppColors.canvas,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(14),
                    borderSide: BorderSide(color: AppColors.border),
                  ),
                ),
              ),
              const SizedBox(height: 6),
              Expanded(
                child: ListView(
                  keyboardDismissBehavior:
                      ScrollViewKeyboardDismissBehavior.onDrag,
                  children: [
                    for (final candidate in candidates)
                      _candidateTile(candidate),
                    if (_loading)
                      const Center(
                        child: Padding(
                          padding: EdgeInsets.all(16),
                          child: CircularProgressIndicator(),
                        ),
                      ),
                    if (_loadFailed)
                      Padding(
                        padding: const EdgeInsets.all(12),
                        child: Text(
                          '기관사 목록을 불러오지 못했어요.',
                          style: TextStyle(color: AppColors.secondaryInk),
                        ),
                      ),
                    if (!_loading && candidates.isEmpty && query.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.all(16),
                        child: Text(
                          '검색 결과가 없어요.',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: AppColors.secondaryInk),
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _candidateTile(_DutyCandidate candidate) {
    final unavailable = candidate.changed || candidate.pending;
    final disabled =
        _busy ||
        unavailable ||
        (!candidate.standalone && (!widget.canRequest || widget.hasPending));
    final times = [
      if (candidate.startTime?.isNotEmpty == true) '출 ${candidate.startTime}',
      if (candidate.endTime?.isNotEmpty == true) '퇴 ${candidate.endTime}',
    ].join(' · ');
    final subtitle = candidate.standalone
        ? null
        : '${candidate.name}${times.isEmpty ? '' : ' · $times'}';
    return Opacity(
      opacity: disabled ? 0.55 : 1,
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 12),
        title: Text(
          candidate.label,
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
        ),
        subtitle: subtitle == null
            ? null
            : Text(
                subtitle,
                style: TextStyle(color: AppColors.secondaryInk, fontSize: 12),
              ),
        trailing: unavailable
            ? Text(
                '변경됨',
                style: TextStyle(
                  color: AppColors.ghostText,
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                ),
              )
            : null,
        enabled: !disabled,
        onTap: disabled ? null : () => _confirmChange(candidate),
      ),
    );
  }
}

int _compareDutyCodes(String left, String right) {
  final chunks = RegExp(r'\d+|\D+');
  final a = chunks
      .allMatches(left.toLowerCase())
      .map((match) => match[0]!)
      .toList();
  final b = chunks
      .allMatches(right.toLowerCase())
      .map((match) => match[0]!)
      .toList();
  for (var i = 0; i < a.length && i < b.length; i++) {
    final aNumber = int.tryParse(a[i]);
    final bNumber = int.tryParse(b[i]);
    final comparison = aNumber != null && bNumber != null
        ? aNumber.compareTo(bNumber)
        : a[i].compareTo(b[i]);
    if (comparison != 0) return comparison;
  }
  return a.length.compareTo(b.length);
}

String _formatDate(String date) {
  final parts = date.split('-').map(int.parse).toList();
  return '${parts[0]}년 ${parts[1]}월 ${parts[2]}일';
}

String _formatCode(String code) => code == '~'
    ? '비번'
    : code == '휴'
    ? '휴무'
    : code;
