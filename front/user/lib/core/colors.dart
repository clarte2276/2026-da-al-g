import 'package:flutter/material.dart';
import 'duty_data.dart';
import 'theme_controller.dart';

/// 라이트/다크 모드에 따라 런타임에 색을 반환한다.
/// (위젯들이 `AppColors.x`를 직접 쓰므로 const가 아닌 getter로 제공)
class AppColors {
  static bool get _dark => ThemeController.instance.isDark;

  // 브랜드 색(공통)
  static const line6Gold = Color(0xffb7922f);

  static Color get ink => _dark ? const Color(0xffece9e2) : const Color(0xff242424);
  static Color get secondaryInk => _dark ? const Color(0xffadadad) : const Color(0xff5c5c5c);
  static Color get canvas => _dark ? const Color(0xff121212) : const Color(0xfff5f4f0);
  static Color get card => _dark ? const Color(0xff1e1e1e) : const Color(0xffffffff);
  static Color get evidence => _dark ? const Color(0xff6b9bd8) : const Color(0xff2e5b9a);
  static Color get softEvidence => _dark ? const Color(0xff232a33) : const Color(0xfff7f9fc);
  static Color get border => _dark ? const Color(0xff3a3a3a) : const Color(0xffe5e2d8);
  static Color get dutyCardBg => _dark ? const Color(0xff2a2a2a) : const Color(0xff242424);
  static Color get dutyMeta => _dark ? const Color(0xffbfbfbf) : const Color(0xffd8d8d8);
  static Color get ghostText => _dark ? const Color(0xff7c7c7c) : const Color(0xff8a8a8a);
  static Color get skeleton => _dark ? const Color(0xff2c2c2c) : const Color(0xffe8e6e0);
}

/// 근무 유형별 대표 색. duty_board/weekly_duty_strip 등에서 공용으로 쓴다.
Color dutyTypeColor(DutyType t) {
  switch (t) {
    case DutyType.day:
      return AppColors.line6Gold;
    case DutyType.night:
      return const Color(0xff3F51B5);
    case DutyType.standby:
      return const Color(0xff009688);
    case DutyType.off:
      return const Color(0xff9E9E9E);
    case DutyType.rest:
      return const Color(0xffBDBDBD);
    case DutyType.designated:
      return const Color(0xff7E57C2);
    case DutyType.unknown:
      return AppColors.border;
  }
}
