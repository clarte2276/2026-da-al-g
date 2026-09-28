import 'package:flutter/material.dart';
import '../core/colors.dart';

class HighlightText extends StatelessWidget {
  const HighlightText(this.text, {super.key});
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: const BoxDecoration(
        color: Color(0xfffff8e1),
        border: Border(left: BorderSide(color: AppColors.line6Gold, width: 4)),
      ),
      child: Text(text),
    );
  }
}
