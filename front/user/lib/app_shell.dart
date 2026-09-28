import 'package:flutter/material.dart';
import 'data/chat_models.dart';
import 'screens/bookmark_screen.dart';
import 'screens/chat_list_screen.dart';
import 'screens/chat_room_screen.dart';
import 'screens/duty_board_screen.dart';
import 'screens/home_screen.dart';
import 'screens/my_page_screen.dart';
import 'screens/regulation_library_screen.dart';
import 'screens/settings_screen.dart';

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _tabIndex = 0;

  void _openTab(int index) => setState(() => _tabIndex = index);

  void _push(Widget screen) =>
      Navigator.push(context, MaterialPageRoute(builder: (_) => screen));

  void _startChatFromText(String text) =>
      _push(ChatRoomScreen(conversation: newConversationFrom(text)));

  @override
  Widget build(BuildContext context) {
    final Widget page = switch (_tabIndex) {
      0 => HomeScreen(
        onAskWithText: _startChatFromText,
        onOpenSchedule: () => _openTab(1),
        onOpenRegulations: () => _push(const RegulationLibraryScreen()),
        onOpenBookmarks: () => _push(const BookmarkScreen()),
        onOpenProfile: () => _push(const MyPageScreen()),
      ),
      1 => const DutyBoardScreen(),
      2 => const ChatListScreen(),
      _ => const SettingsScreen(),
    };

    return Scaffold(
      body: SafeArea(child: page),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tabIndex,
        onDestinationSelected: _openTab,
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home_rounded),
            label: '홈',
          ),
          NavigationDestination(
            icon: Icon(Icons.calendar_month_outlined),
            selectedIcon: Icon(Icons.calendar_month_rounded),
            label: '근무',
          ),
          NavigationDestination(
            icon: Icon(Icons.chat_bubble_outline_rounded),
            selectedIcon: Icon(Icons.chat_bubble_rounded),
            label: '채팅',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            selectedIcon: Icon(Icons.settings_rounded),
            label: '설정',
          ),
        ],
      ),
    );
  }
}
