import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../core/enums.dart';
import '../widgets/app_card.dart';
import '../widgets/app_page.dart';
import '../widgets/page_header.dart';
import '../widgets/section_header.dart';
import '../widgets/today_duty_card.dart';
import '../widgets/train_flow_timeline.dart';
import '../widgets/weekly_grid_view.dart';
import 'duty_board_screen.dart';
import 'schedule_upload_screen.dart';

class ScheduleScreen extends StatelessWidget {
  const ScheduleScreen({
    super.key,
    required this.ready,
    required this.view,
    required this.onUploadComplete,
    required this.onViewChanged,
  });
  final bool ready;
  final ScheduleView view;
  final VoidCallback onUploadComplete;
  final ValueChanged<ScheduleView> onViewChanged;

  @override
  Widget build(BuildContext context) {
    if (!ready || view == ScheduleView.upload) {
      return ScheduleUploadScreen(onUploadComplete: onUploadComplete);
    }

    return AppPage(
      children: [
        const PageHeader(title: '시간표'),
        GestureDetector(
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const DutyBoardScreen()),
          ),
          child: Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.line6Gold,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Row(
              children: [
                const Icon(Icons.grid_view_rounded, color: Colors.white),
                const SizedBox(width: 12),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('근무계획 · 교번표 보기',
                          style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w800)),
                      SizedBox(height: 2),
                      Text('2026년 6월 근무계획 (94명)',
                          style: TextStyle(color: Colors.white70, fontSize: 12)),
                    ],
                  ),
                ),
                const Icon(Icons.arrow_forward_ios_rounded, color: Colors.white, size: 16),
              ],
            ),
          ),
        ),
        AppCard(
          padding: const EdgeInsets.all(4),
          child: Row(
            children: [
              _SegmentTab(label: '오늘', isActive: view == ScheduleView.today, onTap: () => onViewChanged(ScheduleView.today)),
              _SegmentTab(label: '주간', isActive: view == ScheduleView.week, onTap: () => onViewChanged(ScheduleView.week)),
              _SegmentTab(label: '타임라인', isActive: view == ScheduleView.timeline, onTap: () => onViewChanged(ScheduleView.timeline)),
            ],
          ),
        ),
        if (view == ScheduleView.today) ...[
          const TodayDutyCard(isHeader: true),
          const SectionHeader(title: '열차 흐름'),
          const TrainFlowTimeline(),
          const AppCard(
            child: Text('주의 사항\n출입문 점검 강화 · 혼잡 시간대 안내 방송 확인', style: TextStyle(height: 1.5)),
          ),
        ] else if (view == ScheduleView.week)
          const WeeklyGridView()
        else
          const TrainFlowTimeline(),
      ],
    );
  }
}

class _SegmentTab extends StatelessWidget {
  const _SegmentTab({required this.label, required this.isActive, required this.onTap});
  final String label;
  final bool isActive;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            color: isActive ? AppColors.line6Gold : Colors.transparent,
            borderRadius: BorderRadius.circular(14),
          ),
          child: Text(
            label,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: isActive ? Colors.white : AppColors.ink,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ),
    );
  }
}
