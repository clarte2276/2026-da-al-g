import 'package:flutter/material.dart';
import 'core/colors.dart';
import 'core/enums.dart';
import 'screens/bookmark_screen.dart';
import 'data/mock_conversations.dart';
import 'screens/chat_list_screen.dart';
import 'screens/chat_room_screen.dart';
import 'screens/community_board_screen.dart';
import 'screens/community_list_screen.dart';
import 'screens/faq_screen.dart';
import 'screens/home_screen.dart';
import 'screens/my_page_screen.dart';
import 'screens/notification_screen.dart';
import 'screens/regulation_library_screen.dart';
import 'screens/schedule_screen.dart';
import 'screens/settings_screen.dart';

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _tabIndex = 0;
  bool _scheduleReady = false;
  ScheduleView _scheduleView = ScheduleView.today;

  void _openTab(int index) => setState(() => _tabIndex = index);

  void _openScheduleUpload() {
    setState(() {
      _tabIndex = 1;
      _scheduleReady = false;
      _scheduleView = ScheduleView.upload;
    });
  }

  void _openTodaySchedule() {
    setState(() {
      _tabIndex = 1;
      _scheduleReady = true;
      _scheduleView = ScheduleView.today;
    });
  }

  void _push(Widget screen) =>
      Navigator.push(context, MaterialPageRoute(builder: (_) => screen));

  void _startChatFromText(String text) =>
      _push(ChatRoomScreen(conversation: newConversationFrom(text)));

  @override
  Widget build(BuildContext context) {
    final Widget page = switch (_tabIndex) {
      0 => HomeScreen(
        onAskRegulation: () => _openTab(3),
        onAskWithText: _startChatFromText,
        onOpenSchedule: _openTodaySchedule,
        onOpenRegulations: () => _push(const RegulationLibraryScreen()),
        onOpenBookmarks: () => _push(const BookmarkScreen()),
        onOpenNotifications: () => _push(const NotificationScreen()),
        onOpenProfile: () => _push(const MyPageScreen()),
      ),
      1 => ScheduleScreen(
        ready: _scheduleReady,
        view: _scheduleView,
        onUploadComplete: _openTodaySchedule,
        onViewChanged: (view) => setState(() => _scheduleView = view),
      ),
      2 => CommunityListScreen(
        onOpenBoard: (board) => _push(CommunityBoardScreen(title: board)),
        onOpenFAQ: () => _push(const FAQScreen()),
        onOpenBookmarks: () => _push(const BookmarkScreen()),
      ),
      3 => const ChatListScreen(),
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
            label: '시간표',
          ),
          NavigationDestination(
            icon: Icon(Icons.groups_outlined),
            selectedIcon: Icon(Icons.groups_rounded),
            label: '커뮤니티',
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
      floatingActionButton: _tabIndex == 1 && !_scheduleReady
          ? FloatingActionButton.extended(
              onPressed: _openScheduleUpload,
              backgroundColor: AppColors.line6Gold,
              foregroundColor: Colors.white,
              icon: const Icon(Icons.upload_file_rounded),
              label: const Text('근무표 업로드'),
            )
          : null,
    );
  }
}
