import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import '../core/colors.dart';
import '../core/games_logic.dart';
import '../services/life_api.dart';
import 'life_common.dart';

class GamesScreen extends StatelessWidget {
  const GamesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    void open(Widget w) => Navigator.push(context, MaterialPageRoute(builder: (_) => w));
    return lifeScaffold(
      '게임',
      ListView(padding: const EdgeInsets.all(16), children: [
        InfoCard(leading: const Icon(Icons.bolt), title: '반응속도', subtitle: '초록색이 되면 바로 터치', onTap: () => open(const _ReactionGame())),
        const SizedBox(height: 10),
        InfoCard(leading: const Icon(Icons.calculate), title: '암산', subtitle: '30초 동안 최대한 많이', onTap: () => open(const _MathGame())),
        const SizedBox(height: 10),
        InfoCard(leading: const Icon(Icons.palette), title: '색깔 맞추기', subtitle: '글자의 뜻이 아니라 글자색을 고르세요', onTap: () => open(const _ColorGame())),
        const SizedBox(height: 10),
        InfoCard(leading: const Icon(Icons.emoji_events), title: '명예의 전당', onTap: () => open(const _HallOfFame())),
      ]),
    );
  }
}

/// 점수를 올리고 결과를 보여준다.
Future<void> _finish(BuildContext context, String game, int score) async {
  final api = LifeApi();
  final saved = await runAction(context, () => api.postScore(game, score));
  api.close();
  if (!context.mounted) return;
  await showDialog<void>(
    context: context,
    builder: (_) => AlertDialog(
      title: Text(gameNames[game]!),
      content: Text('${lowerIsBetter(game) ? '$score ms' : '$score점'}${saved ? '\n명예의 전당에 기록했습니다' : ''}'),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('확인'))],
    ),
  );
}

class _ReactionGame extends StatefulWidget {
  const _ReactionGame();
  @override
  State<_ReactionGame> createState() => _ReactionGameState();
}

class _ReactionGameState extends State<_ReactionGame> {
  static const _rounds = 3;
  final _results = <int>[];
  Timer? _wait;
  Stopwatch? _watch;
  String _message = '터치해서 시작';

  void _tap() {
    if (_watch != null) {
      _results.add(_watch!.elapsedMilliseconds);
      _watch = null;
      if (_results.length == _rounds) {
        final avg = _results.reduce((a, b) => a + b) ~/ _rounds;
        _results.clear();
        setState(() => _message = '평균 $avg ms · 터치해서 다시');
        _finish(context, 'reaction', avg);
        return;
      }
      setState(() => _message = '${_results.last} ms · 터치해서 다음');
    } else if (_wait != null) {
      _wait!.cancel();
      _wait = null;
      setState(() => _message = '너무 빨라요! 터치해서 다시');
    } else {
      setState(() => _message = '기다리세요… (${_results.length + 1}/$_rounds)');
      _wait = Timer(Duration(milliseconds: 1500 + Random().nextInt(2500)), () {
        _wait = null;
        setState(() {
          _watch = Stopwatch()..start();
          _message = '지금!';
        });
      });
    }
  }

  @override
  void dispose() {
    _wait?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => lifeScaffold(
        '반응속도',
        GestureDetector(
          onTapDown: (_) => _tap(),
          child: Container(
            color: _watch != null ? Colors.green : (_wait != null ? Colors.red.shade400 : AppColors.dutyCardBg),
            alignment: Alignment.center,
            child: Text(_message, style: const TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.w800)),
          ),
        ),
      );
}

/// 30초 제한 게임의 공통 틀.
abstract class _TimedState<T extends StatefulWidget> extends State<T> {
  final random = Random();
  Timer? _timer;
  int left = 0;
  int score = 0;
  String get game;

  bool get playing => left > 0;

  void start() {
    setState(() {
      score = 0;
      left = 30;
      next();
    });
    _timer = Timer.periodic(const Duration(seconds: 1), (t) {
      setState(() => left--);
      if (left == 0) {
        t.cancel();
        _finish(context, game, score);
      }
    });
  }

  void next();

  void answer(bool correct) => setState(() {
        if (correct) score++;
        next();
      });

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Widget frame(String title, Widget board) => lifeScaffold(
        title,
        Padding(
          padding: const EdgeInsets.all(20),
          child: playing
              ? Column(children: [
                  Text('남은 시간 $left초 · $score점', style: TextStyle(color: AppColors.secondaryInk, fontSize: 16)),
                  const SizedBox(height: 24),
                  Expanded(child: board),
                ])
              : Center(child: FilledButton(onPressed: start, child: Text(score > 0 ? '$score점 · 다시 하기' : '시작'))),
        ),
      );
}

class _MathGame extends StatefulWidget {
  const _MathGame();
  @override
  State<_MathGame> createState() => _MathGameState();
}

class _MathGameState extends _TimedState<_MathGame> {
  late MathQuestion _q;
  final _input = TextEditingController();

  @override
  String get game => 'math';

  @override
  void next() {
    _q = MathQuestion.random(random);
    _input.clear();
  }

  @override
  void dispose() {
    _input.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => frame(
        '암산',
        Column(children: [
          Text(playing ? _q.text : '', style: TextStyle(fontSize: 40, fontWeight: FontWeight.w800, color: AppColors.ink)),
          TextField(
            controller: _input,
            autofocus: true,
            keyboardType: TextInputType.number,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 28),
            onSubmitted: (v) => answer(int.tryParse(v) == _q.answer),
            onChanged: (v) {
              if (int.tryParse(v) == _q.answer) answer(true);
            },
          ),
          TextButton(onPressed: () => answer(false), child: const Text('건너뛰기')),
        ]),
      );
}

class _ColorGame extends StatefulWidget {
  const _ColorGame();
  @override
  State<_ColorGame> createState() => _ColorGameState();
}

class _ColorGameState extends _TimedState<_ColorGame> {
  static const _names = ['빨강', '파랑', '초록', '노랑'];
  static const _colors = [Colors.red, Colors.blue, Colors.green, Colors.amber];
  late ColorQuestion _q;

  @override
  String get game => 'color';

  @override
  void next() => _q = ColorQuestion.random(random, _names.length);

  @override
  Widget build(BuildContext context) => frame(
        '색깔 맞추기',
        Column(children: [
          Text(playing ? _names[_q.word] : '', style: TextStyle(fontSize: 48, fontWeight: FontWeight.w900, color: _colors[_q.ink])),
          const SizedBox(height: 32),
          Wrap(spacing: 12, runSpacing: 12, alignment: WrapAlignment.center, children: [
            for (var i = 0; i < _names.length; i++)
              FilledButton(
                style: FilledButton.styleFrom(backgroundColor: AppColors.dutyCardBg, minimumSize: const Size(120, 56)),
                onPressed: () => answer(i == _q.ink),
                child: Text(_names[i]),
              ),
          ]),
        ]),
      );
}

class _HallOfFame extends StatefulWidget {
  const _HallOfFame();
  @override
  State<_HallOfFame> createState() => _HallOfFameState();
}

class _HallOfFameState extends State<_HallOfFame> {
  final _api = LifeApi();
  String _game = 'reaction';
  late Future<List<Json>> _future = _api.fetchScores(_game);

  Future<void> _reload() async {
    setState(() => _future = _api.fetchScores(_game));
    await _future.catchError((_) => <Json>[]);
  }

  @override
  void dispose() {
    _api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => lifeScaffold(
        '명예의 전당',
        Column(children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: SegmentedButton<String>(
              segments: [for (final g in gameNames.entries) ButtonSegment(value: g.key, label: Text(g.value))],
              selected: {_game},
              onSelectionChanged: (s) {
                _game = s.first;
                _reload();
              },
            ),
          ),
          Expanded(
            child: AsyncList(
              future: _future,
              onRefresh: _reload,
              empty: '아직 기록이 없습니다',
              item: (s) => InfoCard(
                title: '${s['name']}',
                trailing: Text(lowerIsBetter(_game) ? '${s['score']} ms' : '${s['score']}점',
                    style: const TextStyle(fontWeight: FontWeight.w800)),
              ),
            ),
          ),
        ]),
      );
}
