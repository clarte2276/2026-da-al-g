import 'package:flutter/material.dart';
import '../core/colors.dart';

class CampusHeader extends StatelessWidget {
  const CampusHeader({super.key, this.onOpenProfile});
  final VoidCallback? onOpenProfile;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Expanded(
          child: Text('Da-Al-G', style: TextStyle(color: AppColors.line6Gold, fontSize: 22, fontWeight: FontWeight.w900)),
        ),
        IconButton(icon: const Icon(Icons.person_outline_rounded), onPressed: onOpenProfile),
      ],
    );
  }
}
