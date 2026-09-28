import 'package:flutter/material.dart';
import '../core/colors.dart';

class BoardHeader extends StatelessWidget {
  const BoardHeader({super.key, required this.title, required this.action});
  final String title, action;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 10),
      child: Row(
        children: [
          Expanded(child: Text(title, style: const TextStyle(fontWeight: FontWeight.w700))),
          Text(action, style: const TextStyle(color: AppColors.line6Gold, fontSize: 12, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
