import 'package:flutter/material.dart';
import 'core/colors.dart';
import 'core/theme_controller.dart';
import 'screens/app_shell_wrapper.dart';
import 'screens/login_screen.dart';
import 'services/auth_session.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ThemeController.instance.init();
  try {
    await AuthSession.restore();
  } catch (_) {
    // Restore failure: fall back to logged-out state.
  }
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
              color: states.contains(WidgetState.selected) ? AppColors.line6Gold : AppColors.secondaryInk,
              fontSize: 13,
              fontWeight: FontWeight.w500,
            ),
          ),
          iconTheme: WidgetStateProperty.resolveWith(
            (states) => IconThemeData(
              color: states.contains(WidgetState.selected) ? AppColors.line6Gold : AppColors.secondaryInk,
              size: 24,
            ),
          ),
        ),
      ),
      home: AuthSession.current != null
          ? const AppShellWrapper()
          : const LoginScreen(),
    );
  }
}
