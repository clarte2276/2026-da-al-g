import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../core/duty_data.dart';
import '../services/auth_session.dart';
import '../services/crew_api.dart';
import '../widgets/app_card.dart';
import '../widgets/page_header.dart';

class ExchangeScreen extends StatefulWidget {
  const ExchangeScreen({super.key});

  @override
  State<ExchangeScreen> createState() => _ExchangeScreenState();
}

class _ExchangeScreenState extends State<ExchangeScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  late CrewApi _api;
  
  List<Map<String, dynamic>>? _allPosts;
  List<Map<String, dynamic>>? _myPosts;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _api = CrewApi();
    _load();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _api.close();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final all = await _api.fetchExchangePosts();
      final mine = await _api.fetchExchangePosts(mine: true);
      if (mounted) {
        setState(() {
          _allPosts = all;
          _myPosts = mine;
        });
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('불러오기 실패: $e')));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _deletePost(String id) async {
    try {
      await _api.deletePost(id);
      _load();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('삭제 실패: $e')));
    }
  }

  Future<void> _respond(String id, String action) async {
    try {
      await _api.respondToPost(id, action: action);
      _load();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('응답 실패: $e')));
    }
  }

  Future<void> _volunteer(String id) async {
    try {
      await _api.volunteer(id);
      _load();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('지원 실패: $e')));
    }
  }

  Future<void> _acceptVolunteer(String id, String vid) async {
    try {
      await _api.acceptVolunteer(id, vid);
      _load();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('수락 실패: $e')));
    }
  }

  void _showCreateSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.canvas,
      builder: (_) => _CreateExchangeSheet(
        api: _api,
        onCreated: () {
          Navigator.pop(context);
          _load();
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(title: const Text('근무 교체', style: TextStyle(fontSize: 16))),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showCreateSheet,
        backgroundColor: AppColors.line6,
        icon: const Icon(Icons.add),
        label: const Text('새 교체 요청'),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
            child: const PageHeader(title: '근무 교체 게시판'),
          ),
          TabBar(
            controller: _tabController,
            labelColor: AppColors.ink,
            unselectedLabelColor: AppColors.secondaryInk,
            indicatorColor: AppColors.line6,
            tabs: const [
              Tab(text: '전체 교체'),
              Tab(text: '내 교체'),
            ],
          ),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                RefreshIndicator(
                  onRefresh: _load,
                  child: _PostList(
                    posts: _allPosts,
                    loading: _loading,
                    onDelete: _deletePost,
                    onRespond: _respond,
                    onVolunteer: _volunteer,
                    onAcceptVolunteer: _acceptVolunteer,
                  ),
                ),
                RefreshIndicator(
                  onRefresh: _load,
                  child: _PostList(
                    posts: _myPosts,
                    loading: _loading,
                    onDelete: _deletePost,
                    onRespond: _respond,
                    onVolunteer: _volunteer,
                    onAcceptVolunteer: _acceptVolunteer,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _PostList extends StatelessWidget {
  const _PostList({
    required this.posts,
    required this.loading,
    required this.onDelete,
    required this.onRespond,
    required this.onVolunteer,
    required this.onAcceptVolunteer,
  });

  final List<Map<String, dynamic>>? posts;
  final bool loading;
  final Function(String) onDelete;
  final Function(String, String) onRespond;
  final Function(String) onVolunteer;
  final Function(String, String) onAcceptVolunteer;

  @override
  Widget build(BuildContext context) {
    if (loading && posts == null) return const Center(child: CircularProgressIndicator());
    if (posts == null || posts!.isEmpty) return ListView(children: const [SizedBox(height: 100), Center(child: Text('게시물이 없습니다.'))]);
    
    final me = AuthSession.current?.user.name;

    return ListView.separated(
      padding: const EdgeInsets.all(16).copyWith(bottom: 80),
      itemCount: posts!.length,
      separatorBuilder: (_, _) => const SizedBox(height: 12),
      itemBuilder: (context, i) {
        final p = posts![i];
        final id = p['id'];
        final type = p['type']; // direct | open
        final status = p['status']; // open | accepted | declined | cancelled
        final targetName = p['target_name'];
        final requester = p['requester_name'];
        final dates = (p['dates'] as List).cast<String>();
        final reqDias = (p['requester_dias'] as List).cast<String>();
        final tgtDias = (p['target_dias'] as List?)?.cast<String>();
        final vols = (p['volunteers'] as List?)?.cast<Map<String, dynamic>>() ?? [];
        
        final amITarget = type == 'direct' && targetName == me;
        final amIRequester = requester == me;

        return AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: status == 'open' ? AppColors.line6.withValues(alpha: 0.1) : AppColors.softEvidence,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      status == 'open' ? '진행중' : status == 'accepted' ? '교체완료' : status == 'declined' ? '거절됨' : '취소됨',
                      style: TextStyle(color: status == 'open' ? AppColors.line6 : AppColors.secondaryInk, fontWeight: FontWeight.bold, fontSize: 12),
                    ),
                  ),
                  if ((amIRequester || (AuthSession.current?.user.isAdmin ?? false)) && status == 'open')
                    IconButton(
                      icon: const Icon(Icons.delete_outline, size: 20),
                      onPressed: () => onDelete(id),
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                type == 'direct' ? '$requester ⇄ $targetName' : '$requester (오픈 교체)',
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              const SizedBox(height: 8),
              for (var j = 0; j < dates.length; j++)
                Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Row(
                    children: [
                      Text(dates[j], style: TextStyle(color: AppColors.secondaryInk, fontSize: 13)),
                      const SizedBox(width: 8),
                      Text(j < reqDias.length ? reqDias[j] : '-', style: const TextStyle(fontWeight: FontWeight.bold)),
                      if (tgtDias != null && j < tgtDias.length) ...[
                        const Icon(Icons.arrow_right_alt, size: 16),
                        Text(tgtDias[j], style: const TextStyle(fontWeight: FontWeight.bold)),
                      ],
                    ],
                  ),
                ),
              if (p['memo'] != null && p['memo'].toString().isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(p['memo'], style: TextStyle(fontSize: 13, color: AppColors.ink)),
              ],
              
              const SizedBox(height: 12),
              
              if (status == 'open') ...[
                if (type == 'direct' && amITarget)
                  Row(
                    children: [
                      Expanded(child: OutlinedButton(onPressed: () => onRespond(id, 'decline'), child: const Text('거절'))),
                      const SizedBox(width: 8),
                      Expanded(child: FilledButton(onPressed: () => onRespond(id, 'accept'), child: const Text('수락'))),
                    ],
                  )
                else if (type == 'open' && !amIRequester && !vols.any((v) => v['person_name'] == me))
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton(onPressed: () => onVolunteer(id), child: const Text('지원하기')),
                  ),
                  
                if (type == 'open' && vols.isNotEmpty) ...[
                  Divider(color: AppColors.border),
                  const Text('지원자', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                  for (final v in vols)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(v['person_name']),
                          if (amIRequester)
                            TextButton(
                              onPressed: () => onAcceptVolunteer(id, v['id']),
                              child: const Text('이 지원자 수락'),
                            )
                          else if (v['person_name'] == me)
                            const Text('내 지원', style: TextStyle(color: AppColors.line6, fontSize: 12)),
                        ],
                      ),
                    ),
                ],
              ],
            ],
          ),
        );
      },
    );
  }
}

class _CreateExchangeSheet extends StatefulWidget {
  const _CreateExchangeSheet({required this.api, required this.onCreated});
  final CrewApi api;
  final VoidCallback onCreated;

  @override
  State<_CreateExchangeSheet> createState() => _CreateExchangeSheetState();
}

class _CreateExchangeSheetState extends State<_CreateExchangeSheet> {
  String _type = 'open'; // 'open' | 'direct'
  Driver? _targetDriver;
  DutyMonth? _monthData;
  final List<String> _dates = [];
  final List<String> _reqDias = [];
  final List<String> _tgtDias = [];
  final TextEditingController _memoCtrl = TextEditingController();
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    DutyRepository.instance.load().then((m) {
      if (mounted) setState(() => _monthData = m);
    });
  }

  void _addDate(String date) {
    if (_dates.contains(date)) return;
    if (_dates.length >= 7) return;
    setState(() {
      _dates.add(date);
      // Auto-fill dias
      final meName = AuthSession.current?.user.name;
      final meDriver = _monthData?.driverNamed(meName);
      final rDuty = meDriver != null ? _monthData?.dutyOn(meDriver, date) : null;
      _reqDias.add(rDuty?.code ?? '');
      
      final tDuty = _targetDriver != null ? _monthData?.dutyOn(_targetDriver!, date) : null;
      _tgtDias.add(tDuty?.code ?? '');
    });
  }

  Future<void> _submit() async {
    if (_dates.isEmpty) return;
    if (_type == 'direct' && _targetDriver == null) return;
    
    setState(() => _loading = true);
    try {
      await widget.api.createExchangePost({
        'type': _type,
        if (_type == 'direct') 'target_name': _targetDriver!.name,
        'dates': _dates,
        'requester_dias': _reqDias,
        if (_type == 'direct') 'target_dias': _tgtDias,
        'memo': _memoCtrl.text,
      });
      widget.onCreated();
    } catch (e) {
      if (mounted) {
        setState(() => _loading = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('생성 실패: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom, left: 20, right: 20, top: 20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('새 근무 교체 요청', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: 'open', label: Text('오픈 교체')),
              ButtonSegment(value: 'direct', label: Text('지정 교체')),
            ],
            selected: {_type},
            onSelectionChanged: (s) => setState(() => _type = s.first),
          ),
          const SizedBox(height: 16),
          if (_type == 'direct') ...[
            OutlinedButton.icon(
              icon: const Icon(Icons.person),
              label: Text(_targetDriver?.name ?? '대상 기관사 선택'),
              onPressed: () async {
                if (_monthData == null) return;
                final picked = await showModalBottomSheet<Driver>(
                  context: context,
                  isScrollControlled: true,
                  builder: (_) => _TargetDriverPicker(drivers: _monthData!.drivers),
                );
                if (picked != null) {
                  setState(() {
                    _targetDriver = picked;
                    // update target dias for already picked dates
                    for (var i = 0; i < _dates.length; i++) {
                      final tDuty = _monthData!.dutyOn(picked, _dates[i]);
                      _tgtDias[i] = tDuty?.code ?? '';
                    }
                  });
                }
              },
            ),
            const SizedBox(height: 16),
          ],
          
          const Text('날짜 및 다이아 (최대 7일)'),
          for (var i = 0; i < _dates.length; i++)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(
                children: [
                  Text(_dates[i], style: const TextStyle(fontSize: 13)),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextField(
                      decoration: const InputDecoration(isDense: true, hintText: '내 다이아'),
                      controller: TextEditingController(text: _reqDias[i])..selection = TextSelection.collapsed(offset: _reqDias[i].length),
                      onChanged: (v) => _reqDias[i] = v,
                    ),
                  ),
                  if (_type == 'direct') ...[
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextField(
                        decoration: const InputDecoration(isDense: true, hintText: '상대 다이아'),
                        controller: TextEditingController(text: _tgtDias[i])..selection = TextSelection.collapsed(offset: _tgtDias[i].length),
                        onChanged: (v) => _tgtDias[i] = v,
                      ),
                    ),
                  ],
                  IconButton(
                    icon: const Icon(Icons.remove_circle_outline, color: Colors.red, size: 20),
                    onPressed: () => setState(() {
                      _dates.removeAt(i);
                      _reqDias.removeAt(i);
                      _tgtDias.removeAt(i);
                    }),
                  ),
                ],
              ),
            ),
            
          if (_dates.length < 7)
            TextButton.icon(
              icon: const Icon(Icons.add),
              label: const Text('날짜 추가'),
              onPressed: () async {
                final picked = await showDatePicker(
                  context: context,
                  initialDate: DateTime.now(),
                  firstDate: DateTime(2020),
                  lastDate: DateTime(2030),
                );
                if (picked != null) {
                  _addDate('${picked.year}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}');
                }
              },
            ),
            
          const SizedBox(height: 16),
          TextField(
            controller: _memoCtrl,
            decoration: const InputDecoration(hintText: '메모 (선택사항)', border: OutlineInputBorder()),
            maxLines: 2,
          ),
          
          const SizedBox(height: 16),
          FilledButton(
            onPressed: _loading || _dates.isEmpty || (_type == 'direct' && _targetDriver == null) ? null : _submit,
            child: _loading ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Text('요청하기'),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}

class _TargetDriverPicker extends StatefulWidget {
  const _TargetDriverPicker({required this.drivers});
  final List<Driver> drivers;

  @override
  State<_TargetDriverPicker> createState() => _TargetDriverPickerState();
}

class _TargetDriverPickerState extends State<_TargetDriverPicker> {
  String _q = '';
  @override
  Widget build(BuildContext context) {
    final me = AuthSession.current?.user.name;
    final filtered = widget.drivers
        .where((d) => d.name != me)
        .where((d) => _q.isEmpty || d.name.contains(_q) || '${d.no}'.contains(_q))
        .toList();
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: SizedBox(
        height: MediaQuery.of(context).size.height * 0.7,
        child: Column(
          children: [
            const SizedBox(height: 12),
            const Text('지정 교체 기관사 선택', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
            Padding(
              padding: const EdgeInsets.all(16),
              child: TextField(
                autofocus: false,
                onChanged: (v) => setState(() => _q = v),
                decoration: InputDecoration(
                  hintText: '이름 검색',
                  prefixIcon: const Icon(Icons.search_rounded),
                  filled: true,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ),
            Expanded(
              child: ListView.builder(
                itemCount: filtered.length,
                itemBuilder: (_, i) {
                  final d = filtered[i];
                  return ListTile(
                    title: Text(d.name),
                    onTap: () => Navigator.pop(context, d),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
