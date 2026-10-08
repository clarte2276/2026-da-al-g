import 'package:flutter/material.dart';
import '../core/colors.dart';
import 'safety_screen.dart';
import 'voice_screen.dart';
import 'menu_screen.dart';
import 'contacts_screen.dart';
import 'edu_screen.dart';
import 'trains_screen.dart';
import 'games_screen.dart';
import 'planner_screen.dart';
import 'healing_card_screen.dart';
import 'news_screen.dart';

class MoreScreen extends StatelessWidget {
  const MoreScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(
        title: Text(
          '더보기',
          style: TextStyle(
            fontWeight: FontWeight.w800,
            color: AppColors.ink,
          ),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
        iconTheme: IconThemeData(color: AppColors.ink),
      ),
      body: GridView.count(
        crossAxisCount: 2,
        padding: const EdgeInsets.all(16.0),
        mainAxisSpacing: 16.0,
        crossAxisSpacing: 16.0,
        childAspectRatio: 1.1,
        children: [
          _buildTile(context, '안전', Icons.security, const SafetyScreen()),
          _buildTile(context, '익명 제보', Icons.campaign, const VoiceScreen()),
          _buildTile(context, '식당 메뉴', Icons.restaurant, const MenuScreen()),
          _buildTile(context, '연락처', Icons.contact_phone, const ContactsScreen()),
          _buildTile(context, '교육 영상', Icons.play_circle_filled, const EduScreen()),
          _buildTile(context, '6호선 실시간', Icons.subway, const TrainsScreen()),
          _buildTile(context, '게임', Icons.videogame_asset, const GamesScreen()),
          _buildTile(context, '할 일 / 일정', Icons.calendar_today, const PlannerScreen()),
          _buildTile(context, '힐링카드', Icons.favorite, const HealingCardScreen()),
          _buildTile(context, '뉴스', Icons.article, const NewsScreen()),
        ],
      ),
    );
  }

  Widget _buildTile(BuildContext context, String title, IconData icon, Widget screen) {
    return InkWell(
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (context) => screen),
        );
      },
      borderRadius: BorderRadius.circular(18),
      child: Container(
        decoration: BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: AppColors.border),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.03),
              blurRadius: 8,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 36,
              color: AppColors.line6,
            ),
            const SizedBox(height: 12),
            Text(
              title,
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w700,
                color: AppColors.ink,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
