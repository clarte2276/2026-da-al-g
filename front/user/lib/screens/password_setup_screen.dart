import 'package:flutter/material.dart';

import '../core/colors.dart';
import '../services/ai_api_client.dart';
import '../services/auth_session.dart';
import '../widgets/app_card.dart';

class PasswordSetupScreen extends StatefulWidget {
  const PasswordSetupScreen({super.key, this.client});

  final AiApiClient? client;

  @override
  State<PasswordSetupScreen> createState() => _PasswordSetupScreenState();
}

class _PasswordSetupScreenState extends State<PasswordSetupScreen> {
  final _current = TextEditingController();
  final _next = TextEditingController();
  final _confirm = TextEditingController();
  late final AiApiClient _client = widget.client ?? AiApiClient();
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
    final error = validatePasswordChange(
      _current.text,
      _next.text,
      _confirm.text,
    );
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
      await AuthSession.passwordChanged();
    } on AiApiException catch (e) {
      setState(
        () => _error = e.statusCode == 400 ? e.message : '비밀번호를 변경하지 못했습니다.',
      );
    } catch (_) {
      if (mounted) setState(() => _error = '서버에 연결하지 못했습니다.');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _logout() async {
    await AuthSession.signOut();
  }

  @override
  Widget build(BuildContext context) => PopScope(
    canPop: false,
    child: Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(
        automaticallyImplyLeading: false,
        title: const Text('비밀번호 설정'),
        actions: [
          TextButton.icon(
            onPressed: _saving ? null : _logout,
            icon: const Icon(Icons.logout_rounded),
            label: const Text('로그아웃'),
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '계정을 계속 사용하려면 새 비밀번호를 설정해 주세요.',
                style: TextStyle(color: AppColors.secondaryInk, height: 1.5),
              ),
              const SizedBox(height: 16),
              AppCard(
                child: Column(
                  children: [
                    _field(_current, '초기 비밀번호'),
                    const SizedBox(height: 12),
                    _field(_next, '새 비밀번호 (8자 이상)'),
                    const SizedBox(height: 12),
                    _field(_confirm, '새 비밀번호 확인'),
                    if (_error != null) ...[
                      const SizedBox(height: 12),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          _error!,
                          style: TextStyle(
                            color: Colors.red.shade400,
                            fontSize: 13,
                          ),
                        ),
                      ),
                    ],
                    const SizedBox(height: 20),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton(
                        onPressed: _saving ? null : _submit,
                        child: _saving
                            ? const SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                ),
                              )
                            : const Text('비밀번호 설정'),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    ),
  );

  Widget _field(TextEditingController controller, String label) => TextField(
    controller: controller,
    obscureText: true,
    enabled: !_saving,
    decoration: InputDecoration(labelText: label),
  );
}
