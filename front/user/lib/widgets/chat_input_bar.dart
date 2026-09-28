import 'package:flutter/material.dart';
import '../core/colors.dart';

/// 채팅 화면과 홈 화면이 공유하는 채팅 입력 바.
/// 텍스트 입력 + 전송 버튼. 전송 시 [onSubmit]에 트림된 텍스트를 넘기고 입력을 비운다.
class ChatInputBar extends StatefulWidget {
  const ChatInputBar({
    super.key,
    required this.onSubmit,
    this.hintText = '규정에 대해 질문해보세요…',
    this.focusNode,
  });

  final ValueChanged<String> onSubmit;
  final String hintText;
  final FocusNode? focusNode;

  @override
  State<ChatInputBar> createState() => _ChatInputBarState();
}

class _ChatInputBarState extends State<ChatInputBar> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _submit() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    _controller.clear();
    widget.onSubmit(text);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.canvas,
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
      child: Container(
        decoration: BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: AppColors.border),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.04),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            const SizedBox(width: 16),
            Expanded(
              child: TextField(
                controller: _controller,
                focusNode: widget.focusNode,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _submit(),
                decoration: InputDecoration(
                  hintText: widget.hintText,
                  hintStyle: TextStyle(color: AppColors.ghostText, fontSize: 14),
                  border: InputBorder.none,
                  isDense: true,
                  contentPadding: const EdgeInsets.symmetric(vertical: 14),
                ),
              ),
            ),
            const SizedBox(width: 8),
            GestureDetector(
              onTap: _submit,
              child: Container(
                margin: const EdgeInsets.all(6),
                width: 34,
                height: 34,
                decoration: const BoxDecoration(
                  color: AppColors.line6Gold,
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.arrow_upward_rounded, color: Colors.white, size: 18),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
