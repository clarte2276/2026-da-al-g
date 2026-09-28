import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../widgets/app_card.dart';
import '../widgets/app_page.dart';
import '../widgets/page_header.dart';

class ScheduleUploadScreen extends StatelessWidget {
  const ScheduleUploadScreen({super.key, required this.onUploadComplete});
  final VoidCallback onUploadComplete;

  @override
  Widget build(BuildContext context) {
    return AppPage(
      children: [
        const PageHeader(title: '근무표 업로드'),
        AppCard(
          child: Column(
            children: [
              const Icon(Icons.upload_file_rounded, size: 48, color: AppColors.line6Gold),
              const SizedBox(height: 16),
              const Text('6호선 승무 근무표 파일을 선택하세요', textAlign: TextAlign.center),
              const SizedBox(height: 20),
              ElevatedButton(onPressed: onUploadComplete, child: const Text('샘플 파일 분석')),
            ],
          ),
        ),
      ],
    );
  }
}
