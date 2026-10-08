import 'package:flutter/material.dart';
import 'core/colors.dart';
import 'core/personal_store.dart';
import 'core/theme_controller.dart';
import 'screens/app_shell_wrapper.dart';
import 'screens/login_screen.dart';
import 'screens/password_setup_screen.dart';
import 'services/ai_api_client.dart';
import 'services/auth_session.dart';
import 'services/duty_alarm.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ThemeController.instance.init();
  try {
    await AuthSession.restore();
  } catch (_) {
    // Restore failure: fall back to logged-out state.
  }
  await PersonalStore.instance.init();
  await DutyAlarm.instance.init();
  runApp(const DaAlGApp());
}

class DaAlGApp extends StatelessWidget {
  const DaAlGApp({super.key});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: ThemeController.instance,
      builder: (context, _) => _buildApp(),
    );
  }

  Widget _buildApp() {
    final dark = ThemeController.instance.isDark;
    return MaterialApp(
      title: 'Da-Al-G',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: AppColors.line6Gold,
          brightness: dark ? Brightness.dark : Brightness.light,
          surface: AppColors.card,
          primary: AppColors.line6GoldDeep,
          onSurface: AppColors.ink,
        ),
        scaffoldBackgroundColor: AppColors.canvas,
        fontFamily: 'Pretendard',
        appBarTheme: AppBarTheme(
          backgroundColor: AppColors.card,
          foregroundColor: AppColors.ink,
          elevation: 0,
          centerTitle: false,
          titleTextStyle: TextStyle(
            color: AppColors.ink,
            fontSize: 20,
            fontWeight: FontWeight.w700,
          ),
        ),
        navigationBarTheme: NavigationBarThemeData(
          height: 88,
          backgroundColor: AppColors.card,
          indicatorColor: Colors.transparent,
          labelTextStyle: WidgetStateProperty.resolveWith(
            (states) => TextStyle(
              color: states.contains(WidgetState.selected)
                  ? AppColors.line6Gold
                  : AppColors.secondaryInk,
              fontSize: 13,
              fontWeight: FontWeight.w500,
            ),
          ),
          iconTheme: WidgetStateProperty.resolveWith(
            (states) => IconThemeData(
              color: states.contains(WidgetState.selected)
                  ? AppColors.line6Gold
                  : AppColors.secondaryInk,
              size: 24,
            ),
          ),
        ),
      ),
      home: const AuthHome(),
      builder: (context, child) =>
          AuthSessionGate(child: child ?? const SizedBox.shrink()),
    );
  }
}

class AuthSessionGate extends StatelessWidget {
  const AuthSessionGate({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) => ValueListenableBuilder<AuthResponse?>(
    valueListenable: AuthSession.listenable,
    builder: (context, session, _) {
      final blocked = session?.user.mustChangePassword == true;
      return Stack(
        fit: StackFit.expand,
        children: [
          Offstage(offstage: blocked, child: child),
          if (blocked) const PasswordSetupScreen(),
        ],
      );
    },
  );
}

class AuthHome extends StatelessWidget {
  const AuthHome({super.key});

  @override
  Widget build(BuildContext context) => ValueListenableBuilder<AuthResponse?>(
    valueListenable: AuthSession.listenable,
    builder: (context, session, _) =>
        session == null ? const LoginScreen() : const AppShellWrapper(),
  );
}
