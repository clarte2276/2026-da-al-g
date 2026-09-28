import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../services/ai_api_client.dart';
import '../services/auth_session.dart';
import 'login_screen.dart';

class MyPageScreen extends StatelessWidget {
  const MyPageScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final user = AuthSession.current?.user;
    final name = user?.name.isNotEmpty == true ? user!.name : '홍길동';
    final line = user?.line.isNotEmpty == true ? user!.line : '6호선';
    final employeeId = user?.employeeId.isNotEmpty == true
        ? user!.employeeId
        : '20240001';
    final initial = name.isNotEmpty ? name.substring(0, 1) : '홍';

    return Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(title: const Text('마이페이지')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          children: [
            // Profile card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: AppColors.dutyCardBg,
                borderRadius: BorderRadius.circular(18),
              ),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 30,
                    backgroundColor: AppColors.line6Gold.withValues(alpha: 0.2),
                    child: Text(
                      initial,
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: AppColors.line6Gold,
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          name,
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w800,
                            color: Colors.white,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '서울메트로 $line',
                          style: TextStyle(
                            fontSize: 13,
                            color: AppColors.dutyMeta,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '사번 $employeeId',
                          style: TextStyle(
                            fontSize: 13,
                            color: AppColors.ghostText,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            _MenuSection(
              title: '정보',
              items: [
                _MenuItem(
                  icon: Icons.train_rounded,
                  label: '소속 노선',
                  trailing: line,
                ),
                const _MenuItem(
                  icon: Icons.info_outline_rounded,
                  label: '앱 버전',
                  trailing: 'v0.1.0',
                ),
              ],
            ),
            const SizedBox(height: 12),

            _MenuSection(
              title: '계정',
              items: [
                _MenuItem(
                  icon: Icons.lock_outline_rounded,
                  label: '비밀번호 변경',
                  onTap: () => showDialog<void>(
                    context: context,
                    builder: (_) => const _PasswordDialog(),
                  ),
                ),
                _MenuItem(
                  icon: Icons.logout_rounded,
                  label: '로그아웃',
                  labelColor: AppColors.evidence,
                  onTap: () => _confirmLogout(context),
                ),
              ],
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  void _confirmLogout(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text(
          '로그아웃',
          style: TextStyle(fontWeight: FontWeight.w700),
        ),
        content: const Text('정말 로그아웃 하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('취소', style: TextStyle(color: AppColors.secondaryInk)),
          ),
          TextButton(
            onPressed: () {
              AuthSession.signOut();
              Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(builder: (_) => const LoginScreen()),
                (_) => false,
              );
            },
            child: const Text(
              '로그아웃',
              style: TextStyle(
                color: AppColors.line6Gold,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MenuSection extends StatelessWidget {
  const _MenuSection({required this.title, required this.items});
  final String title;
  final List<_MenuItem> items;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 4, bottom: 8),
          child: Text(
            title,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: AppColors.secondaryInk,
            ),
          ),
        ),
        Container(
          decoration: BoxDecoration(
            color: AppColors.card,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.border),
          ),
          child: Column(
            children: List.generate(items.length, (i) {
              return Column(
                children: [
                  items[i],
                  if (i < items.length - 1)
                    const Divider(height: 1, indent: 52),
                ],
              );
            }),
          ),
        ),
      ],
    );
  }
}

class _MenuItem extends StatelessWidget {
  const _MenuItem({
    required this.icon,
    required this.label,
    this.trailing,
    this.labelColor,
    this.onTap,
  });
  final IconData icon;
  final String label;
  final String? trailing;
  final Color? labelColor;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    // 카드 배경 위에서도 탭 물결이 보이도록 자체 Material을 둔다.
    return Material(
      type: MaterialType.transparency,
      child: ListTile(
        leading: Icon(icon, color: labelColor ?? AppColors.line6Gold, size: 22),
        title: Text(
          label,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w500,
            color: labelColor ?? AppColors.ink,
          ),
        ),
        trailing: trailing != null
            ? Text(
                trailing!,
                style: TextStyle(fontSize: 13, color: AppColors.ghostText),
              )
            : Icon(
                Icons.chevron_right_rounded,
                color: AppColors.ghostText,
                size: 18,
              ),
        onTap: onTap,
        dense: true,
      ),
    );
  }
}

class _PasswordDialog extends StatefulWidget {
  const _PasswordDialog();

  @override
  State<_PasswordDialog> createState() => _PasswordDialogState();
}

class _PasswordDialogState extends State<_PasswordDialog> {
  final _current = TextEditingController();
  final _next = TextEditingController();
  final _confirm = TextEditingController();
  final _client = AiApiClient();
  bool _saving = false;
  String? _error;

  @override
  void dispose() {
    _current.dispose();
    _next.dispose();
    _confirm.dispose();
    _client.close();
    super.dispose();
  }

  Future<void> _submit() async {
    final error = switch ((_current.text, _next.text, _confirm.text)) {
      ('', _, _) => '현재 비밀번호를 입력해 주세요.',
      (_, final n, _) when n.length < 8 => '새 비밀번호는 8자 이상이어야 합니다.',
      (_, final n, final c) when n != c => '새 비밀번호가 서로 다릅니다.',
      _ => null,
    };
    if (error != null) {
      setState(() => _error = error);
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await _client.changePassword(
        currentPassword: _current.text,
        newPassword: _next.text,
      );
      if (!mounted) return;
      final messenger = ScaffoldMessenger.of(context);
      Navigator.pop(context);
      messenger.showSnackBar(
        const SnackBar(content: Text('비밀번호를 바꿨습니다. 다른 기기는 로그아웃됩니다.')),
      );
    } on AiApiException catch (e) {
      // 400은 서버가 사용자용 문구를 보낸다(현재 비밀번호 불일치 등).
      setState(() => _error = e.statusCode == 400 ? e.message : '비밀번호를 바꾸지 못했습니다.');
    } catch (_) {
      setState(() => _error = '서버에 연결하지 못했습니다.');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Widget _field(TextEditingController c, String label) => TextField(
    controller: c,
    obscureText: true,
    enabled: !_saving,
    decoration: InputDecoration(labelText: label),
  );

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('비밀번호 변경'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _field(_current, '현재 비밀번호'),
            _field(_next, '새 비밀번호 (8자 이상)'),
            _field(_confirm, '새 비밀번호 확인'),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: TextStyle(color: Colors.red.shade400, fontSize: 13)),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _saving ? null : () => Navigator.pop(context),
          child: const Text('취소'),
        ),
        TextButton(
          onPressed: _saving ? null : _submit,
          child: const Text('변경'),
        ),
      ],
    );
  }
}
