import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../core/colors.dart';
import '../services/auth_session.dart';
import '../services/crew_api.dart';
import '../widgets/page_header.dart';

class StandbyCoverageScreen extends StatefulWidget {
  const StandbyCoverageScreen({super.key});

  @override
  State<StandbyCoverageScreen> createState() => _StandbyCoverageScreenState();
}

class _StandbyCoverageScreenState extends State<StandbyCoverageScreen> {
  late CrewApi _api;
  String _selectedDate = _todayDateString();
  List<Map<String, dynamic>>? _items;
  String? _error;
  bool _loading = false;

  static String _todayDateString() {
    final now = DateTime.now();
    return '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
  }

  @override
  void initState() {
    super.initState();
    _api = CrewApi();
    _load();
  }

  @override
  void dispose() {
    _api.close();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final items = await _api.fetchStandbyCoverage(date: _selectedDate);
      if (mounted) setState(() => _items = items);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _pickDate() async {
    final initDate = DateTime.parse(_selectedDate);
    final picked = await showDatePicker(
      context: context,
      initialDate: initDate,
      firstDate: DateTime(2020),
      lastDate: DateTime(2030),
    );
    if (picked != null) {
      final newDate = '${picked.year}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}';
      if (newDate != _selectedDate) {
        setState(() => _selectedDate = newDate);
        _load();
      }
    }
  }

  Future<void> _uploadPhoto() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.gallery, imageQuality: 70);
    if (picked == null) return;
    
    setState(() => _loading = true);
    try {
      final bytes = await picked.readAsBytes();
      await _api.uploadStandbyCoverage(
        date: _selectedDate,
        fileBytes: bytes,
        filename: picked.name,
      );
      _load();
    } catch (e) {
      if (mounted) {
        setState(() => _loading = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('업로드 실패: $e')));
      }
    }
  }

  Future<void> _deleteItem(String id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('삭제'),
        content: const Text('정말로 삭제하시겠습니까?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('취소')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('삭제', style: TextStyle(color: Colors.red))),
        ],
      ),
    );
    
    if (confirm != true) return;
    
    setState(() => _loading = true);
    try {
      await _api.deleteStandbyCoverage(id);
      _load();
    } catch (e) {
      if (mounted) {
        setState(() => _loading = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('삭제 실패: $e')));
      }
    }
  }

  void _showImage(String url) {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        backgroundColor: Colors.transparent,
        insetPadding: EdgeInsets.zero,
        child: Stack(
          fit: StackFit.expand,
          children: [
            InteractiveViewer(
              child: Image.network(
                url,
                headers: {
                  if (AuthSession.current?.accessToken != null)
                    'Authorization': 'Bearer ${AuthSession.current!.accessToken}'
                },
              ),
            ),
            Positioned(
              top: 40,
              right: 20,
              child: IconButton(
                icon: const Icon(Icons.close, color: Colors.white, size: 30),
                onPressed: () => Navigator.pop(context),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.canvas,
      appBar: AppBar(title: const Text('대기충당확인', style: TextStyle(fontSize: 16))),
      floatingActionButton: FloatingActionButton(
        onPressed: _uploadPhoto,
        backgroundColor: AppColors.line6,
        child: const Icon(Icons.add_a_photo),
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: const PageHeader(title: '대기충당확인'),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: OutlinedButton.icon(
              icon: const Icon(Icons.calendar_today),
              label: Text(_selectedDate),
              onPressed: _pickDate,
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.ink,
                side: BorderSide(color: AppColors.border),
                padding: const EdgeInsets.symmetric(vertical: 12),
              ),
            ),
          ),
          if (_loading && _items == null)
            const Expanded(child: Center(child: CircularProgressIndicator())),
          if (_error != null)
            Expanded(child: Center(child: Text('에러 발생:\n$_error'))),
          if (_items != null && _items!.isEmpty && !_loading)
            const Expanded(child: Center(child: Text('해당 날짜에 등록된 사진이 없습니다.'))),
          if (_items != null && _items!.isNotEmpty)
            Expanded(
              child: GridView.builder(
                padding: const EdgeInsets.all(16),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  childAspectRatio: 0.8,
                ),
                itemCount: _items!.length,
                itemBuilder: (context, i) {
                  final item = _items![i];
                  final isMine = item['mine'] == true;
                  final url = _api.standbyCoverageImageUrl(item['id']);
                  return Card(
                    clipBehavior: Clip.antiAlias,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    child: Stack(
                      fit: StackFit.expand,
                      children: [
                        GestureDetector(
                          onTap: () => _showImage(url),
                          child: Image.network(
                            url,
                            fit: BoxFit.cover,
                            headers: {
                              if (AuthSession.current?.accessToken != null)
                                'Authorization': 'Bearer ${AuthSession.current!.accessToken}'
                            },
                          ),
                        ),
                        Positioned(
                          bottom: 0,
                          left: 0,
                          right: 0,
                          child: Container(
                            padding: const EdgeInsets.all(8),
                            color: Colors.black54,
                            child: Row(
                              children: [
                                Expanded(
                                  child: Text(
                                    item['uploader_name'] ?? '알 수 없음',
                                    style: const TextStyle(color: Colors.white, fontSize: 13),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                                if (isMine)
                                  IconButton(
                                    icon: const Icon(Icons.delete, color: Colors.white70, size: 20),
                                    padding: EdgeInsets.zero,
                                    constraints: const BoxConstraints(),
                                    onPressed: () => _deleteItem(item['id']),
                                  ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
        ],
      ),
    );
  }
}
