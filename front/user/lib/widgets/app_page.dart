import 'package:flutter/material.dart';

class AppPage extends StatelessWidget {
  const AppPage({super.key, required this.children, this.horizontalPadding = 16});
  final List<Widget> children;
  final double horizontalPadding;

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding: EdgeInsets.fromLTRB(horizontalPadding, 12, horizontalPadding, 24),
      itemBuilder: (context, index) => children[index],
      separatorBuilder: (context, index) => const SizedBox(height: 16),
      itemCount: children.length,
    );
  }
}
