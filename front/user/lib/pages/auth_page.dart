import 'package:flutter/material.dart';

import '../core/models/rag_models.dart';
import '../core/services/rag_api_client.dart';
import 'chat_page.dart';

class AuthGate extends StatefulWidget {
  const AuthGate({super.key, this.api});

  final RagApiClient? api;

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  late final RagApiClient _api = widget.api ?? RagApiClient();
  AuthSession? _session;
  bool _registerMode = false;
  bool _loading = false;
  String? _error;

  void _signedIn(AuthSession session) {
    if (!mounted) return;
    setState(() {
      _session = session;
      _error = null;
    });
  }

  void _sessionExpired() {
    _api.clearToken();
    if (mounted) setState(() => _session = null);
  }

  Future<void> _logout() async {
    try {
      await _api.logout();
    } catch (_) {
      // Clearing the local session is enough when the server is unavailable.
    } finally {
      if (mounted) setState(() => _session = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    final session = _session;
    if (session != null) {
      return ChatPage(
        api: _api,
        user: session.user,
        onLogout: _logout,
        onSessionExpired: _sessionExpired,
      );
    }
    return AuthPage(
      registerMode: _registerMode,
      loading: _loading,
      error: _error,
      onRegisterModeChanged: (value) => setState(() {
        _registerMode = value;
        _error = null;
      }),
      onSubmit: (username, password, displayName) async {
        if (_loading) return;
        setState(() {
          _loading = true;
          _error = null;
        });
        try {
          final session = _registerMode
              ? await _api.register(
                  username,
                  password,
                  displayName: displayName,
                )
              : await _api.login(username, password);
          _signedIn(session);
        } catch (error) {
          if (mounted) {
            setState(() {
              _error = error is RagApiException
                  ? error.message
                  : '서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.';
            });
          }
        } finally {
          if (mounted) setState(() => _loading = false);
        }
      },
    );
  }
}

class AuthPage extends StatefulWidget {
  const AuthPage({
    required this.registerMode,
    required this.loading,
    required this.error,
    required this.onRegisterModeChanged,
    required this.onSubmit,
    super.key,
  });

  final bool registerMode;
  final bool loading;
  final String? error;
  final ValueChanged<bool> onRegisterModeChanged;
  final Future<void> Function(String username, String password, String? displayName)
      onSubmit;

  @override
  State<AuthPage> createState() => _AuthPageState();
}

class _AuthPageState extends State<AuthPage> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _displayNameController = TextEditingController();

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _displayNameController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    await widget.onSubmit(
      _usernameController.text.trim(),
      _passwordController.text,
      _displayNameController.text.trim().isEmpty
          ? null
          : _displayNameController.text.trim(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(28),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Icon(
                          Icons.auto_awesome_rounded,
                          size: 42,
                          color: theme.colorScheme.primary,
                        ),
                        const SizedBox(height: 14),
                        Text(
                          'Da-Al-G AI',
                          textAlign: TextAlign.center,
                          style: theme.textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          widget.registerMode
                              ? '새 계정을 만들어 시작하세요.'
                              : '문서 지식 검색을 시작하려면 로그인하세요.',
                          textAlign: TextAlign.center,
                          style: theme.textTheme.bodyMedium,
                        ),
                        const SizedBox(height: 24),
                        if (widget.error != null) ...[
                          Text(
                            widget.error!,
                            style: TextStyle(color: theme.colorScheme.error),
                          ),
                          const SizedBox(height: 12),
                        ],
                        TextFormField(
                          controller: _usernameController,
                          enabled: !widget.loading,
                          autofocus: true,
                          textInputAction: widget.registerMode
                              ? TextInputAction.next
                              : TextInputAction.next,
                          autofillHints: const [AutofillHints.username],
                          decoration: const InputDecoration(
                            labelText: '아이디',
                            prefixIcon: Icon(Icons.person_outline),
                          ),
                          validator: (value) {
                            if (value == null || value.trim().isEmpty) {
                              return '아이디를 입력해 주세요.';
                            }
                            if (value.trim().length < 3) {
                              return '아이디는 3자 이상 입력해 주세요.';
                            }
                            return null;
                          },
                        ),
                        if (widget.registerMode) ...[
                          const SizedBox(height: 12),
                          TextFormField(
                            controller: _displayNameController,
                            enabled: !widget.loading,
                            textInputAction: TextInputAction.next,
                            decoration: const InputDecoration(
                              labelText: '표시 이름 (선택)',
                              prefixIcon: Icon(Icons.badge_outlined),
                            ),
                          ),
                        ],
                        const SizedBox(height: 12),
                        TextFormField(
                          controller: _passwordController,
                          enabled: !widget.loading,
                          obscureText: true,
                          textInputAction: TextInputAction.done,
                          autofillHints: const [AutofillHints.password],
                          onFieldSubmitted: (_) => _submit(),
                          decoration: const InputDecoration(
                            labelText: '비밀번호',
                            prefixIcon: Icon(Icons.lock_outline),
                          ),
                          validator: (value) {
                            if (value == null || value.isEmpty) {
                              return '비밀번호를 입력해 주세요.';
                            }
                            if (widget.registerMode && value.length < 8) {
                              return '비밀번호는 8자 이상 입력해 주세요.';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 20),
                        FilledButton(
                          onPressed: widget.loading ? null : _submit,
                          child: widget.loading
                              ? const SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                )
                              : Text(widget.registerMode ? '회원가입' : '로그인'),
                        ),
                        const SizedBox(height: 4),
                        TextButton(
                          onPressed: widget.loading
                              ? null
                              : () => widget.onRegisterModeChanged(
                                  !widget.registerMode,
                                ),
                          child: Text(
                            widget.registerMode
                                ? '이미 계정이 있나요? 로그인'
                                : '계정이 없나요? 회원가입',
                          ),
                        ),
                        if (!widget.registerMode) ...[
                          const SizedBox(height: 12),
                          Text(
                            '개발 테스트 계정: test / test',
                            textAlign: TextAlign.center,
                            style: theme.textTheme.bodySmall,
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
