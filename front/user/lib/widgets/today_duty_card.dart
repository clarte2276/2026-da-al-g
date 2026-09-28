import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../core/duty_data.dart';
import '../services/auth_session.dart';
import 'status_pill.dart';

/// 근무표 JSON에서 로그인한 사용자의 오늘 근무를 보여준다.
class TodayDutyCard extends StatelessWidget {
  const TodayDutyCard({super.key, this.onTap});
  final VoidCallback? onTap;

  static const _weekdays = ['월', '화', '수', '목', '금', '토', '일'];

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: AppColors.dutyCardBg,
          borderRadius: BorderRadius.circular(18),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Wrap(
                    spacing: 8,
                    runSpacing: 6,
                    children: [
                      const StatusPill(label: '오늘 근무', color: Colors.white, bgColor: Color(0xff3d3d3d)),
                      StatusPill(
                        label: '${now.month}/${now.day} (${_weekdays[now.weekday - 1]})',
                        color: AppColors.line6Gold,
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.arrow_forward_ios_rounded, size: 14, color: Colors.white54),
              ],
            ),
            const SizedBox(height: 20),
            FutureBuilder<DutyMonth>(
              future: DutyRepository.instance.load(),
              builder: (context, snap) {
                final (title, meta) = _describe(snap, now);
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(color: Colors.white, fontSize: 19, fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 12),
                    Text(meta, style: TextStyle(color: AppColors.dutyMeta, fontSize: 14)),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  (String, String) _describe(AsyncSnapshot<DutyMonth> snap, DateTime now) {
    if (snap.hasError) return ('근무표를 불러오지 못했습니다', '근무 탭에서 다시 확인하세요');
    final data = snap.data;
    if (data == null) return ('불러오는 중…', '');
    final me = data.driverNamed(AuthSession.current?.user.name);
    if (me == null) return ('근무표에서 내 이름을 찾지 못했습니다', '근무 탭에서 기관사를 선택해 확인하세요');
    final duty = me.days[dutyDateKey(now)];
    if (duty == null) return ('오늘 근무 정보가 없습니다', '등록된 근무표: ${data.month}');
    final turn = duty.turn == null ? '' : ' · 교번 ${duty.turn}';
    final detail = data.turns[duty.turn];
    // 교번 시각이 아직 더미면 보여주지 않는다.
    final meta = detail != null && !data.turnDetailIsDummy
        ? '출무 ${detail.depart} · ${detail.route}'
        : '${data.office} · ${me.name}';
    return ('${duty.type.label}$turn', meta);
  }
}
