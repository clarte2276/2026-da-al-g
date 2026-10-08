import 'dart:math';

/// 미니게임 규칙. 화면과 분리해 테스트한다.
const gameNames = {'reaction': '반응속도', 'math': '암산', 'color': '색깔 맞추기'};

/// 반응속도는 ms라 낮을수록 좋다.
bool lowerIsBetter(String game) => game == 'reaction';

class MathQuestion {
  MathQuestion(this.text, this.answer);
  final String text;
  final int answer;

  factory MathQuestion.random(Random r) {
    switch (r.nextInt(3)) {
      case 0:
        final a = 10 + r.nextInt(90), b = 10 + r.nextInt(90);
        return MathQuestion('$a + $b', a + b);
      case 1:
        final a = 20 + r.nextInt(80), b = 1 + r.nextInt(a);
        return MathQuestion('$a - $b', a - b);
      default:
        final a = 2 + r.nextInt(18), b = 2 + r.nextInt(8);
        return MathQuestion('$a × $b', a * b);
    }
  }
}

/// 글자 뜻과 글자색이 다른 문제(스트룹). 정답은 글자색.
class ColorQuestion {
  ColorQuestion(this.word, this.ink);
  final int word;
  final int ink;

  factory ColorQuestion.random(Random r, int count) {
    final word = r.nextInt(count);
    final ink = (word + 1 + r.nextInt(count - 1)) % count;
    return ColorQuestion(word, ink);
  }
}
