import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../services/ai_api_client.dart';
import '../services/auth_session.dart';
import 'app_shell_wrapper.dart';
import 'signup_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _idController = TextEditingController();
  final _pwController = TextEditingController();
  final _apiClient = AiApiClient();
  bool _obscure = true;
  bool _isSubmitting = false;
  String? _errorText;

  @override
  void dispose() {
    _idController.dispose();
    _pwController.dispose();
    _apiClient.close();
    super.dispose();
  }

  Future<void> _login() async {
    final identifier = _idController.text.trim();
    final password = _pwController.text;
    if (identifier.isEmpty || password.isEmpty) {
      setState(() => _errorText = '사번 또는 이메일과 비밀번호를 입력해 주세요.');
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorText = null;
    });

    try {
      final response = await _apiClient.login(
        identifier: identifier,
        password: password,
      );
      AuthSession.signIn(response);
      if (!mounted) {
        return;
      }
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const AppShellWrapper()),
      );
    } on AiApiException catch (error) {
      if (!mounted) {
        return;
      }
      setState(() => _errorText = _friendlyAuthError(error.message));
    } catch (_) {
      if (!mounted) {
        return;
      }
      setState(() => _errorText = '로그인 중 오류가 발생했습니다.');
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  // MVP: '비밀번호 찾기'를 누르면 인증 없이 바로 앱으로 진입한다.
  void _skipLogin() {
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => const AppShellWrapper()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.canvas,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 64),
              // Logo
              Row(
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: AppColors.line6Gold,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.train_rounded,
                      color: Colors.white,
                      size: 26,
                    ),
                  ),
                  const SizedBox(width: 12),
                  const Text(
                    'Da-Al-G',
                    style: TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.w900,
                      color: AppColors.line6Gold,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                '서울 6호선 승무원을 위한\n규정·시간표 통합 플랫폼',
                style: TextStyle(
                  fontSize: 15,
                  color: AppColors.secondaryInk,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 48),

              // Fields
              const _FieldLabel(text: '사번 또는 이메일'),
              const SizedBox(height: 8),
              _InputField(
                controller: _idController,
                hint: '20240001 또는 name@smco.kr',
                keyboardType: TextInputType.emailAddress,
                enabled: !_isSubmitting,
              ),
              const SizedBox(height: 20),
              const _FieldLabel(text: '비밀번호'),
              const SizedBox(height: 8),
              _InputField(
                controller: _pwController,
                hint: '비밀번호 입력',
                obscure: _obscure,
                enabled: !_isSubmitting,
                suffix: IconButton(
                  icon: Icon(
                    _obscure
                        ? Icons.visibility_off_outlined
                        : Icons.visibility_outlined,
                    size: 20,
                  ),
                  color: AppColors.ghostText,
                  onPressed: () => setState(() => _obscure = !_obscure),
                ),
              ),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: _isSubmitting ? null : _skipLogin,
                  child: Text(
                    '비밀번호 찾기',
                    style: TextStyle(color: AppColors.ghostText, fontSize: 13),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              if (_errorText != null) ...[
                Text(
                  _errorText!,
                  style: TextStyle(
                    color: Colors.red.shade400,
                    fontSize: 13,
                    height: 1.4,
                  ),
                ),
                const SizedBox(height: 12),
              ],

              // Login button
              SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton(
                  onPressed: _isSubmitting ? null : _login,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.line6Gold,
                    foregroundColor: Colors.white,
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                  child: _isSubmitting
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Text(
                          '로그인',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                ),
              ),
              const SizedBox(height: 24),

              // Sign up link
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    '계정이 없으신가요?',
                    style: TextStyle(
                      color: AppColors.secondaryInk,
                      fontSize: 14,
                    ),
                  ),
                  TextButton(
                    onPressed: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const SignUpScreen()),
                    ),
                    child: const Text(
                      '회원가입',
                      style: TextStyle(
                        color: AppColors.line6Gold,
                        fontWeight: FontWeight.w700,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  String _friendlyAuthError(String message) {
    switch (message) {
      case 'invalid identifier or password':
        return '사번 또는 비밀번호가 올바르지 않습니다.';
      default:
        return message;
    }
  }
}

class _FieldLabel extends StatelessWidget {
  const _FieldLabel({required this.text});
  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: TextStyle(
        fontSize: 13,
        fontWeight: FontWeight.w600,
        color: AppColors.ink,
      ),
    );
  }
}

class _InputField extends StatelessWidget {
  const _InputField({
    required this.controller,
    required this.hint,
    this.obscure = false,
    this.suffix,
    this.keyboardType,
    this.enabled = true,
  });
  final TextEditingController controller;
  final String hint;
  final bool obscure;
  final Widget? suffix;
  final TextInputType? keyboardType;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: TextField(
        controller: controller,
        obscureText: obscure,
        keyboardType: keyboardType,
        enabled: enabled,
        style: const TextStyle(fontSize: 15),
        decoration: InputDecoration(
          hintText: hint,
          hintStyle: TextStyle(color: AppColors.ghostText, fontSize: 14),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 16,
            vertical: 14,
          ),
          suffixIcon: suffix,
        ),
      ),
    );
  }
}
