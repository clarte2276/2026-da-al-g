import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../services/life_api.dart';
import '../widgets/app_page.dart';
import '../widgets/campus_header.dart';
import '../widgets/chat_input_bar.dart';
import '../widgets/page_header.dart';
import '../widgets/quick_action_grid.dart';
import '../widgets/section_header.dart';
import '../widgets/today_duty_card.dart';
import '../widgets/weekly_duty_strip.dart';
import '../widgets/weather_card.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({
    super.key,
    required this.onAskWithText,
    required this.onOpenSchedule,
    required this.onOpenBookmarks,
    required this.onOpenRegulations,
    required this.onOpenProfile,
    required this.onOpenMore,
  });
  final ValueChanged<String> onAskWithText;
  final VoidCallback onOpenSchedule;
  final VoidCallback onOpenBookmarks;
  final VoidCallback onOpenRegulations;
  final VoidCallback onOpenProfile;
  final VoidCallback onOpenMore;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<Map<String, dynamic>> _alerts = [];
  bool _isLoadingAlerts = true;

  @override
  void initState() {
    super.initState();
    _fetchAlerts();
  }

  Future<void> _fetchAlerts() async {
    try {
      final lifeApi = LifeApi();
      final alerts = await lifeApi.fetchAlerts();
      if (mounted) {
        setState(() {
          _alerts = alerts;
          _isLoadingAlerts = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _isLoadingAlerts = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        if (!_isLoadingAlerts && _alerts.isNotEmpty)
          Container(
            color: Colors.red.shade50,
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            child: Row(
              children: [
                Icon(Icons.warning_amber_rounded, color: Colors.red.shade700, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '${_alerts.first['message'] ?? '안전 알림이 있습니다'}${_alerts.length > 1 ? ' 외 ${_alerts.length - 1}건' : ''}',
                    style: TextStyle(color: Colors.red.shade900, fontSize: 13, fontWeight: FontWeight.w700),
                  ),
                ),
              ],
            ),
          ),
        Expanded(
          child: AppPage(
            horizontalPadding: 20,
            children: [
              CampusHeader(onOpenProfile: widget.onOpenProfile),
              const WeatherCard(),
              const PageHeader(title: '오늘의 승무 지원'),
              TodayDutyCard(onTap: widget.onOpenSchedule),
              QuickActionGrid(
                onOpenSchedule: widget.onOpenSchedule,
                onOpenBookmarks: widget.onOpenBookmarks,
                onOpenRegulations: widget.onOpenRegulations,
                onOpenMore: widget.onOpenMore,
              ),
              SectionHeader(title: '이번주 근무', action: '근무 달력', onActionTap: widget.onOpenSchedule),
              WeeklyDutyStrip(onTapDay: widget.onOpenSchedule),
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
        ChatInputBar(onSubmit: widget.onAskWithText),
      ],
    );
  }
}
