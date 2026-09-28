import 'package:flutter/material.dart';
import '../core/colors.dart';

class ChatComposer extends StatelessWidget {
  const ChatComposer({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          const Expanded(
            child: TextField(decoration: InputDecoration(hintText: '메시지 입력', border: InputBorder.none)),
          ),
          Container(
            decoration: const BoxDecoration(color: AppColors.line6Gold, shape: BoxShape.circle),
            child: IconButton(icon: const Icon(Icons.arrow_upward, color: Colors.white), onPressed: () {}),
          ),
        ],
      ),
    );
  }
}
