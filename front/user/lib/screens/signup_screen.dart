import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../services/ai_api_client.dart';
import '../services/auth_session.dart';
import 'app_shell_wrapper.dart';

class SignUpScreen extends StatefulWidget {
  const SignUpScreen({super.key});

  @override
  State<SignUpScreen> createState() => _SignUpScreenState();
}

class _SignUpScreenState extends State<SignUpScreen> {
  final _nameController = TextEditingController();
  final _idController = TextEditingController();
  final _emailController = TextEditingController();
  final _pwController = TextEditingController();
  final _pwConfirmController = TextEditingController();
  final _apiClient = AiApiClient();
  bool _obscurePw = true;
  bool _obscureConfirm = true;
  bool _isSubmitting = false;
  String? _errorText;
  String _selectedLine = '6호선';

  static const _lines = ['6호선'];

  @override
  void dispose() {
    _nameController.dispose();
    _idController.dispose();
    _emailController.dispose();
    _pwController.dispose();
    _pwConfirmController.dispose();
    _apiClient.close();
    super.dispose();
  }

  Future<void> _submit() async {
    final name = _nameController.text.trim();
    final employeeId = _idController.text.trim();
    final email = _emailController.text.trim();
    final password = _pwController.text;
    final passwordConfirm = _pwConfirmController.text;

    final validationError = _validate(
      name: name,
      employeeId: employeeId,
      email: email,
      password: password,
      passwordConfirm: passwordConfirm,
    );
    if (validationError != null) {
      setState(() => _errorText = validationError);
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorText = null;
    });

    try {
      final response = await _apiClient.signUp(
        name: name,
        employeeId: employeeId,
        email: email,
        password: password,
        line: _selectedLine,
      );
      AuthSession.signIn(response);
      if (!mounted) {
        return;
      }
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (_) => const AppShellWrapper()),
        (_) => false,
      );
    } on AiApiException catch (error) {
      if (!mounted) {
        return;
      }
      setState(() => _errorText = _friendlySignUpError(error.message));
    } catch (_) {
      if (!mounted) {
        return;
      }
      setState(() => _errorText = '회원가입 중 오류가 발생했습니다.');
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(title: const Text('회원가입'), leading: const BackButton()),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _Section(
              title: '기본 정보',
              children: [
                _FormRow(
                  label: '이름',
                  child: _Field(
                    controller: _nameController,
                    hint: '홍길동',
                    enabled: !_isSubmitting,
                  ),
                ),
                _FormRow(
                  label: '사번',
                  child: _Field(
                    controller: _idController,
                    hint: '20240001',
                    keyboardType: TextInputType.number,
                    enabled: !_isSubmitting,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            _Section(
              title: '소속 노선',
              children: [
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: _lines.map((line) {
                    final selected = line == _selectedLine;
                    return GestureDetector(
                      onTap: _isSubmitting
                          ? null
                          : () => setState(() => _selectedLine = line),
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 14,
                          vertical: 8,
                        ),
                        decoration: BoxDecoration(
                          color: selected
                              ? AppColors.line6Gold
                              : AppColors.card,
                          borderRadius: BorderRadius.circular(99),
                          border: Border.all(
                            color: selected
                                ? AppColors.line6Gold
                                : AppColors.border,
                          ),
                        ),
                        child: Text(
                          line,
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: selected
                                ? Colors.white
                                : AppColors.secondaryInk,
                          ),
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ],
            ),
            const SizedBox(height: 20),
            _Section(
              title: '계정 정보',
              children: [
                _FormRow(
                  label: '이메일',
                  child: _Field(
                    controller: _emailController,
                    hint: 'name@smco.kr',
                    keyboardType: TextInputType.emailAddress,
                    enabled: !_isSubmitting,
                  ),
                ),
                _FormRow(
                  label: '비밀번호',
                  child: _Field(
                    controller: _pwController,
                    hint: '8자 이상',
                    obscure: _obscurePw,
                    enabled: !_isSubmitting,
                    suffix: _EyeButton(
                      obscure: _obscurePw,
                      onTap: () => setState(() => _obscurePw = !_obscurePw),
                    ),
                  ),
                ),
                _FormRow(
                  label: '비밀번호 확인',
                  child: _Field(
                    controller: _pwConfirmController,
                    hint: '비밀번호 재입력',
                    obscure: _obscureConfirm,
                    enabled: !_isSubmitting,
                    suffix: _EyeButton(
                      obscure: _obscureConfirm,
                      onTap: () =>
                          setState(() => _obscureConfirm = !_obscureConfirm),
                    ),
                  ),
                ),
              ],
            ),
            if (_errorText != null) ...[
              const SizedBox(height: 14),
              Text(
                _errorText!,
                style: TextStyle(
                  color: Colors.red.shade400,
                  fontSize: 13,
                  height: 1.4,
                ),
              ),
            ],
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton(
                onPressed: _isSubmitting ? null : _submit,
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
                        '가입 완료',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
              ),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  String? _validate({
    required String name,
    required String employeeId,
    required String email,
    required String password,
    required String passwordConfirm,
  }) {
    if (name.isEmpty ||
        employeeId.isEmpty ||
        email.isEmpty ||
        password.isEmpty ||
        passwordConfirm.isEmpty) {
      return '모든 항목을 입력해 주세요.';
    }
    if (!email.contains('@')) {
      return '올바른 이메일 주소를 입력해 주세요.';
    }
    if (password.length < 8) {
      return '비밀번호는 8자 이상이어야 합니다.';
    }
    if (password != passwordConfirm) {
      return '비밀번호 확인이 일치하지 않습니다.';
    }
    return null;
  }

  String _friendlySignUpError(String message) {
    switch (message) {
      case 'employee_id already exists':
        return '이미 가입된 사번입니다.';
      case 'email already exists':
        return '이미 가입된 이메일입니다.';
      case 'password must be at least 8 characters':
        return '비밀번호는 8자 이상이어야 합니다.';
      case 'email must be valid':
        return '올바른 이메일 주소를 입력해 주세요.';
      default:
        return message;
    }
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.children});
  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w700,
            color: AppColors.secondaryInk,
          ),
        ),
        const SizedBox(height: 10),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.card,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.border),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: children,
          ),
        ),
      ],
    );
  }
}

class _FormRow extends StatelessWidget {
  const _FormRow({required this.label, required this.child});
  final String label;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: AppColors.secondaryInk,
            ),
          ),
          const SizedBox(height: 6),
          child,
        ],
      ),
    );
  }
}

class _Field extends StatelessWidget {
  const _Field({
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
        color: AppColors.canvas,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.border),
      ),
      child: TextField(
        controller: controller,
        obscureText: obscure,
        keyboardType: keyboardType,
        enabled: enabled,
        style: const TextStyle(fontSize: 14),
        decoration: InputDecoration(
          hintText: hint,
          hintStyle: TextStyle(color: AppColors.ghostText, fontSize: 13),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 12,
            vertical: 11,
          ),
          suffixIcon: suffix,
          isDense: true,
        ),
      ),
    );
  }
}

class _EyeButton extends StatelessWidget {
  const _EyeButton({required this.obscure, required this.onTap});
  final bool obscure;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: Icon(
        obscure ? Icons.visibility_off_outlined : Icons.visibility_outlined,
        size: 18,
      ),
      color: AppColors.ghostText,
      onPressed: onTap,
    );
  }
}
