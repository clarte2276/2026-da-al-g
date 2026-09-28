import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../services/auth_session.dart';
import 'login_screen.dart';

class MyPageScreen extends StatelessWidget {
  const MyPageScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final user = AuthSession.current?.user;
    final name = user?.name.isNotEmpty == true ? user!.name : '홍길동';
    final line = user?.line.isNotEmpty == true ? user!.line : '6호선';
    final employeeId = user?.employeeId.isNotEmpty == true
        ? user!.employeeId
        : '20240001';
    final initial = name.isNotEmpty ? name.substring(0, 1) : '홍';

    return Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(title: const Text('마이페이지')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          children: [
            // Profile card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: AppColors.dutyCardBg,
                borderRadius: BorderRadius.circular(18),
              ),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 30,
                    backgroundColor: AppColors.line6Gold.withValues(alpha: 0.2),
                    child: Text(
                      initial,
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: AppColors.line6Gold,
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        name,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '서울메트로 $line',
                        style: TextStyle(
                          fontSize: 13,
                          color: AppColors.dutyMeta,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '사번 $employeeId',
                        style: TextStyle(
                          fontSize: 12,
                          color: AppColors.ghostText,
                        ),
                      ),
                    ],
                  ),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(
                      Icons.edit_outlined,
                      color: Colors.white54,
                      size: 20,
                    ),
                    onPressed: () => _showComingSoon(context),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            _MenuSection(
              title: '내 정보',
              items: [
                _MenuItem(
                  icon: Icons.person_outline_rounded,
                  label: '프로필 수정',
                  onTap: () => _showComingSoon(context),
                ),
                _MenuItem(
                  icon: Icons.lock_outline_rounded,
                  label: '비밀번호 변경',
                  onTap: () => _showComingSoon(context),
                ),
              ],
            ),
            const SizedBox(height: 12),

            _MenuSection(
              title: '앱 설정',
              items: [
                _MenuItem(
                  icon: Icons.train_rounded,
                  label: '소속 노선',
                  trailing: '6호선',
                  onTap: () => _showComingSoon(context),
                ),
                _MenuItem(
                  icon: Icons.notifications_outlined,
                  label: '알림 설정',
                  onTap: () => _showComingSoon(context),
                ),
                _MenuItem(
                  icon: Icons.description_outlined,
                  label: '규정 버전',
                  trailing: '2026.04',
                  onTap: () => _showComingSoon(context),
                ),
              ],
            ),
            const SizedBox(height: 12),

            _MenuSection(
              title: '기타',
              items: [
                _MenuItem(
                  icon: Icons.campaign_outlined,
                  label: '공지사항',
                  onTap: () => _showComingSoon(context),
                ),
                _MenuItem(
                  icon: Icons.help_outline_rounded,
                  label: '이용 문의',
                  onTap: () => _showComingSoon(context),
                ),
                _MenuItem(
                  icon: Icons.info_outline_rounded,
                  label: '앱 버전',
                  trailing: 'v0.1.0',
                  onTap: () => _showComingSoon(context),
                ),
              ],
            ),
            const SizedBox(height: 12),

            _MenuSection(
              title: '계정',
              items: [
                _MenuItem(
                  icon: Icons.logout_rounded,
                  label: '로그아웃',
                  labelColor: AppColors.evidence,
                  onTap: () => _confirmLogout(context),
                ),
                _MenuItem(
                  icon: Icons.person_remove_outlined,
                  label: '회원탈퇴',
                  labelColor: Colors.red.shade400,
                  onTap: () => _showComingSoon(context),
                ),
              ],
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  void _showComingSoon(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('준비 중입니다.')),
    );
  }

  void _confirmLogout(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text(
          '로그아웃',
          style: TextStyle(fontWeight: FontWeight.w700),
        ),
        content: const Text('정말 로그아웃 하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(
              '취소',
              style: TextStyle(color: AppColors.secondaryInk),
            ),
          ),
          TextButton(
            onPressed: () {
              AuthSession.signOut();
              Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(builder: (_) => const LoginScreen()),
                (_) => false,
              );
            },
            child: const Text(
              '로그아웃',
              style: TextStyle(
                color: AppColors.line6Gold,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MenuSection extends StatelessWidget {
  const _MenuSection({required this.title, required this.items});
  final String title;
  final List<_MenuItem> items;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 4, bottom: 8),
          child: Text(
            title,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: AppColors.secondaryInk,
            ),
          ),
        ),
        Container(
          decoration: BoxDecoration(
            color: AppColors.card,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.border),
          ),
          child: Column(
            children: List.generate(items.length, (i) {
              return Column(
                children: [
                  items[i],
                  if (i < items.length - 1)
                    const Divider(height: 1, indent: 52),
                ],
              );
            }),
          ),
        ),
      ],
    );
  }
}

class _MenuItem extends StatelessWidget {
  const _MenuItem({
    required this.icon,
    required this.label,
    this.trailing,
    this.labelColor,
    required this.onTap,
  });
  final IconData icon;
  final String label;
  final String? trailing;
  final Color? labelColor;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: labelColor ?? AppColors.line6Gold, size: 22),
      title: Text(
        label,
        style: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w500,
          color: labelColor ?? AppColors.ink,
        ),
      ),
      trailing: trailing != null
          ? Text(
              trailing!,
              style: TextStyle(fontSize: 13, color: AppColors.ghostText),
            )
          : Icon(
              Icons.chevron_right_rounded,
              color: AppColors.ghostText,
              size: 18,
            ),
      onTap: onTap,
      dense: true,
    );
  }
}
