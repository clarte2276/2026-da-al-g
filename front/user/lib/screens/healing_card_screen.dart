import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../core/local_life_store.dart';
import 'life_common.dart';

String won(int v) => '${v.toString().replaceAllMapped(RegExp(r'\B(?=(\d{3})+$)'), (_) => ',')}원';

class HealingCardScreen extends StatefulWidget {
  const HealingCardScreen({super.key});
  @override
  State<HealingCardScreen> createState() => _HealingCardScreenState();
}

class _HealingCardScreenState extends State<HealingCardScreen> {
  HealingCard? _card;
  DateTime _month = DateTime.now();

  @override
  void initState() {
    super.initState();
    HealingCard.load().then((c) => setState(() => _card = c));
  }

  Future<void> _update(void Function(HealingCard) change) async {
    setState(() => change(_card!));
    await _card!.save();
  }

  Future<void> _setLimit() async {
    final v = await promptFields(context, '월 한도', ['금액 (원)'], initial: ['${_card!.limit}']);
    final limit = int.tryParse(v?.first.replaceAll(',', '') ?? '');
    if (limit != null) _update((c) => c.limit = limit);
  }

  Future<void> _add() async {
    final v = await promptFields(context, '사용 내역 추가', ['금액 (원)', '사용처']);
    final amount = int.tryParse(v?.first.replaceAll(',', '') ?? '');
    if (amount != null && amount > 0) _update((c) => c.add(_month, amount, v![1]));
  }

  @override
  Widget build(BuildContext context) {
    final card = _card;
    if (card == null) return lifeScaffold('힐링카드', const Center(child: CircularProgressIndicator()));
    final items = card.month(_month);
    final balance = card.balance(_month);
    final isThisMonth = monthKey(_month) == monthKey(DateTime.now());
    return lifeScaffold(
      '힐링카드',
      ListView(padding: const EdgeInsets.all(16), children: [
        Row(children: [
          IconButton(
            icon: const Icon(Icons.chevron_left),
            onPressed: () => setState(() => _month = DateTime(_month.year, _month.month - 1)),
          ),
          Expanded(child: Text('${_month.year}년 ${_month.month}월', textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.w800))),
          IconButton(
            icon: const Icon(Icons.chevron_right),
            onPressed: isThisMonth ? null : () => setState(() => _month = DateTime(_month.year, _month.month + 1)),
          ),
        ]),
        Card(
          elevation: 0,
          color: AppColors.dutyCardBg,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('잔액', style: TextStyle(color: AppColors.dutyMeta)),
              Text(won(balance),
                  style: TextStyle(fontSize: 30, fontWeight: FontWeight.w800, color: balance < 0 ? Colors.redAccent : Colors.white)),
              const SizedBox(height: 8),
              Text('한도 ${won(card.limit)} · 사용 ${won(card.spent(_month))}', style: TextStyle(color: AppColors.dutyMeta)),
              TextButton(onPressed: _setLimit, child: const Text('한도 설정')),
            ]),
          ),
        ),
        const SizedBox(height: 8),
        if (items.isEmpty)
          Padding(padding: const EdgeInsets.all(32), child: Text('사용 내역이 없습니다', textAlign: TextAlign.center, style: TextStyle(color: AppColors.ghostText))),
        for (var i = items.length - 1; i >= 0; i--)
          ListTile(
            title: Text(won(items[i]['amount'] as int)),
            subtitle: Text('${items[i]['memo']} · ${shortTime(items[i]['at'])}'),
            trailing: IconButton(icon: const Icon(Icons.delete_outline), onPressed: () => _update((c) => c.remove(_month, i))),
          ),
      ]),
      fab: FloatingActionButton(onPressed: _add, child: const Icon(Icons.add)),
    );
  }
}
