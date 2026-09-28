import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../widgets/app_page.dart';
import '../widgets/campus_header.dart';
import '../widgets/chat_input_bar.dart';
import '../widgets/page_header.dart';
import '../widgets/quick_action_grid.dart';
import '../widgets/section_header.dart';
import '../widgets/today_duty_card.dart';
import '../widgets/weekly_duty_strip.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({
    super.key,
    required this.onAskRegulation,
    required this.onAskWithText,
    required this.onOpenSchedule,
    required this.onOpenBookmarks,
    required this.onOpenRegulations,
    required this.onOpenNotifications,
    required this.onOpenProfile,
  });
  final VoidCallback onAskRegulation;
  final ValueChanged<String> onAskWithText;
  final VoidCallback onOpenSchedule;
  final VoidCallback onOpenBookmarks;
  final VoidCallback onOpenRegulations;
  final VoidCallback onOpenNotifications;
  final VoidCallback onOpenProfile;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(
          child: AppPage(
            horizontalPadding: 20,
            children: [
              CampusHeader(onOpenNotifications: onOpenNotifications, onOpenProfile: onOpenProfile),
              Text(_greeting(), style: TextStyle(color: AppColors.secondaryInk, fontSize: 15)),
              const PageHeader(title: '오늘의 승무 지원'),
              TodayDutyCard(onTap: onOpenSchedule),
              QuickActionGrid(
                onAskRegulation: onAskRegulation,
                onOpenSchedule: onOpenSchedule,
                onOpenBookmarks: onOpenBookmarks,
                onOpenRegulations: onOpenRegulations,
              ),
              SectionHeader(title: '내 시간표', action: '시간표 보기', onActionTap: onOpenSchedule),
              WeeklyDutyStrip(onTapDay: onOpenSchedule),
            ],
          ),
        ),
        // 하단 바 바로 위: 채팅에서 질문하기 (채팅 화면의 입력 바 재사용)
        Padding(
          padding: EdgeInsets.fromLTRB(20, 0, 20, 0),
          child: Row(
            children: [
              Icon(Icons.smart_toy_outlined, size: 16, color: AppColors.secondaryInk),
              SizedBox(width: 6),
              Text('채팅에서 질문하기',
                  style: TextStyle(color: AppColors.secondaryInk, fontSize: 13, fontWeight: FontWeight.w700)),
            ],
          ),
        ),
        ChatInputBar(onSubmit: onAskWithText),
      ],
    );
  }

  String _greeting() {
    final hour = DateTime.now().hour;
    if (hour >= 5 && hour < 11) return '좋은 아침입니다';
    if (hour >= 11 && hour < 14) return '좋은 점심입니다';
    if (hour >= 14 && hour < 18) return '좋은 오후입니다';
    if (hour >= 18 && hour < 22) return '좋은 저녁입니다';
    return '늦은 밤이네요, 수고하셨어요';
  }
}
