import 'package:flutter/material.dart';

import '../core/colors.dart';
import '../services/ai_api_client.dart';
import '../widgets/app_card.dart';

class InquiryScreen extends StatefulWidget {
  const InquiryScreen({super.key, this.client});

  final AiApiClient? client;

  @override
  State<InquiryScreen> createState() => _InquiryScreenState();
}

class _InquiryScreenState extends State<InquiryScreen> {
  late final AiApiClient _client = widget.client ?? AiApiClient();
  late Future<List<Map<String, dynamic>>> _future = _client.fetchInquiries();

  @override
  void dispose() {
    _client.close();
    super.dispose();
  }

  Future<void> _reload() async {
    final future = _client.fetchInquiries();
    setState(() => _future = future);
    try {
      await future;
    } catch (_) {}
  }

  Future<void> _create() async {
    final created = await Navigator.push<bool>(
      context,
      MaterialPageRoute(builder: (_) => _NewInquiryScreen(client: _client)),
    );
    if (created == true) _reload();
  }

  Future<void> _open(Map<String, dynamic> inquiry) async {
    await Navigator.push<void>(
      context,
      MaterialPageRoute(
        builder: (_) => _InquiryDetailScreen(inquiry: inquiry, client: _client),
      ),
    );
    if (mounted) _reload();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: AppColors.canvas,
    appBar: AppBar(title: const Text('고객문의')),
    body: FutureBuilder<List<Map<String, dynamic>>>(
      future: _future,
      builder: (context, snapshot) => RefreshIndicator(
        onRefresh: _reload,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          children: [
            if (snapshot.connectionState == ConnectionState.waiting)
              const Padding(
                padding: EdgeInsets.only(top: 100),
                child: Center(child: CircularProgressIndicator()),
              )
            else if (snapshot.hasError)
              Padding(
                padding: const EdgeInsets.only(top: 80),
                child: Column(
                  children: [
                    const Text('문의를 불러오지 못했습니다.'),
                    TextButton(onPressed: _reload, child: const Text('다시 시도')),
                  ],
                ),
              )
            else if (snapshot.data?.isEmpty ?? true)
              const Padding(
                padding: EdgeInsets.only(top: 80),
                child: Center(child: Text('등록한 고객문의가 없습니다.')),
              )
            else
              for (final inquiry in snapshot.data!)
                Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: _InquiryListCard(
                    inquiry: inquiry,
                    onTap: () => _open(inquiry),
                  ),
                ),
          ],
        ),
      ),
    ),
    floatingActionButton: FloatingActionButton.extended(
      onPressed: _create,
      icon: const Icon(Icons.edit_rounded),
      label: const Text('문의 작성'),
    ),
  );
}

class _InquiryListCard extends StatelessWidget {
  const _InquiryListCard({required this.inquiry, required this.onTap});

  final Map<String, dynamic> inquiry;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final feedback = inquiry['kind'] == 'feedback';
    final replies = (inquiry['replies'] as List? ?? const [])
        .whereType<Map<String, dynamic>>();
    final answered = replies.any((reply) => reply['from_admin'] == true);
    return AppCard(
      padding: EdgeInsets.zero,
      child: Material(
        type: MaterialType.transparency,
        child: ListTile(
          onTap: onTap,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 16,
            vertical: 8,
          ),
          title: Row(
            children: [
              _Badge(label: feedback ? '답변 피드백' : '문의'),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  inquiry['title'] as String? ?? '',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
              ),
            ],
          ),
          subtitle: Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Row(
              children: [
                Text(
                  inquiryDate(inquiry['created_at']),
                  style: TextStyle(color: AppColors.ghostText, fontSize: 12),
                ),
                const Spacer(),
                Text(
                  answered ? '답변 완료' : '답변 대기',
                  style: TextStyle(
                    color: answered
                        ? AppColors.line6GoldDeep
                        : AppColors.secondaryInk,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
          trailing: Icon(
            Icons.chevron_right_rounded,
            color: AppColors.ghostText,
          ),
        ),
      ),
    );
  }
}

class _InquiryDetailScreen extends StatefulWidget {
  const _InquiryDetailScreen({required this.inquiry, required this.client});

  final Map<String, dynamic> inquiry;
  final AiApiClient client;

  @override
  State<_InquiryDetailScreen> createState() => _InquiryDetailScreenState();
}

class _InquiryDetailScreenState extends State<_InquiryDetailScreen> {
  late Map<String, dynamic> _inquiry = widget.inquiry;
  final _reply = TextEditingController();
  bool _sending = false;

  @override
  void dispose() {
    _reply.dispose();
    super.dispose();
  }

  Future<void> _sendReply() async {
    final body = _reply.text.trim();
    if (body.isEmpty) return;
    setState(() => _sending = true);
    try {
      final updated = await widget.client.replyToInquiry(
        '${_inquiry['id']}',
        body,
      );
      if (!mounted) return;
      setState(() {
        _inquiry = updated;
        _reply.clear();
      });
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('답글을 보내지 못했습니다.')));
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final feedback = _inquiry['kind'] == 'feedback';
    final replies = (_inquiry['replies'] as List? ?? const [])
        .whereType<Map<String, dynamic>>();
    return Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(title: const Text('문의 내용')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _Badge(label: feedback ? '답변 피드백' : '문의'),
                const SizedBox(height: 10),
                Text(
                  _inquiry['title'] as String? ?? '',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  inquiryDate(_inquiry['created_at']),
                  style: TextStyle(color: AppColors.ghostText, fontSize: 12),
                ),
                const Divider(height: 24),
                Text(_inquiry['body'] as String? ?? ''),
                if (feedback) ...[
                  const SizedBox(height: 16),
                  _detailLabel('평가'),
                  Text(switch (_inquiry['rating']) {
                    'up' => '도움이 됐어요',
                    'down' => '아쉬워요',
                    _ => '평가 없음',
                  }),
                  const SizedBox(height: 12),
                  _detailLabel('질문'),
                  Text(_inquiry['question'] as String? ?? ''),
                  const SizedBox(height: 12),
                  _detailLabel('답변'),
                  Text(_excerpt(_inquiry['answer'] as String? ?? '')),
                ],
              ],
            ),
          ),
          const SizedBox(height: 16),
          Text(
            '답변 내역',
            style: TextStyle(
              color: AppColors.secondaryInk,
              fontSize: 14,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 8),
          if (replies.isEmpty)
            AppCard(
              child: Text(
                '아직 답변이 없습니다.',
                style: TextStyle(color: AppColors.secondaryInk),
              ),
            )
          else
            for (final reply in replies)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: AppCard(
                  background: reply['from_admin'] == true
                      ? AppColors.softEvidence
                      : AppColors.card,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            reply['from_admin'] == true ? '관리자' : '나',
                            style: const TextStyle(fontWeight: FontWeight.w700),
                          ),
                          const Spacer(),
                          Text(
                            inquiryDate(reply['created_at']),
                            style: TextStyle(
                              color: AppColors.ghostText,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(reply['body'] as String? ?? ''),
                    ],
                  ),
                ),
              ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: TextField(
                  controller: _reply,
                  minLines: 1,
                  maxLines: 4,
                  enabled: !_sending,
                  decoration: const InputDecoration(
                    hintText: '답글을 입력해 주세요',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                ),
              ),
              IconButton(
                tooltip: '답글 보내기',
                onPressed: _sending ? null : _sendReply,
                icon: const Icon(Icons.send_rounded),
                color: AppColors.line6GoldDeep,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _NewInquiryScreen extends StatefulWidget {
  const _NewInquiryScreen({required this.client});

  final AiApiClient client;

  @override
  State<_NewInquiryScreen> createState() => _NewInquiryScreenState();
}

class _NewInquiryScreenState extends State<_NewInquiryScreen> {
  final _title = TextEditingController();
  final _body = TextEditingController();
  bool _sending = false;
  String? _error;

  @override
  void dispose() {
    _title.dispose();
    _body.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final title = _title.text.trim();
    final body = _body.text.trim();
    if (title.isEmpty || body.isEmpty) {
      setState(() => _error = '제목과 내용을 입력해 주세요.');
      return;
    }
    setState(() {
      _sending = true;
      _error = null;
    });
    try {
      await widget.client.createInquiry(title: title, body: body);
      if (mounted) Navigator.pop(context, true);
    } on AiApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = '문의를 보내지 못했습니다.');
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: AppColors.canvas,
    appBar: AppBar(title: const Text('문의 작성')),
    body: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        AppCard(
          child: Column(
            children: [
              TextField(
                controller: _title,
                maxLength: 200,
                enabled: !_sending,
                decoration: const InputDecoration(
                  labelText: '제목',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _body,
                maxLength: 4000,
                minLines: 8,
                maxLines: 12,
                enabled: !_sending,
                decoration: const InputDecoration(
                  labelText: '문의 내용',
                  alignLabelWithHint: true,
                  border: OutlineInputBorder(),
                ),
              ),
              if (_error != null) ...[
                Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    _error!,
                    style: TextStyle(color: Colors.red.shade400, fontSize: 13),
                  ),
                ),
                const SizedBox(height: 8),
              ],
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: _sending ? null : _submit,
                  child: _sending
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('문의 보내기'),
                ),
              ),
            ],
          ),
        ),
      ],
    ),
  );
}

class _Badge extends StatelessWidget {
  const _Badge({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) => DecoratedBox(
    decoration: BoxDecoration(
      color: AppColors.softEvidence,
      borderRadius: BorderRadius.circular(20),
    ),
    child: Padding(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
      child: Text(
        label,
        style: TextStyle(
          color: AppColors.evidence,
          fontSize: 11,
          fontWeight: FontWeight.w600,
        ),
      ),
    ),
  );
}

Widget _detailLabel(String label) => Padding(
  padding: const EdgeInsets.only(bottom: 4),
  child: Text(
    label,
    style: TextStyle(
      color: AppColors.secondaryInk,
      fontSize: 12,
      fontWeight: FontWeight.w700,
    ),
  ),
);

String inquiryDate(Object? value) {
  final date = DateTime.tryParse(value as String? ?? '')?.toLocal();
  if (date == null) return '';
  String two(int n) => n.toString().padLeft(2, '0');
  return '${date.year}.${two(date.month)}.${two(date.day)}';
}

String _excerpt(String text) =>
    text.length > 500 ? '${text.substring(0, 500)}…' : text;
