# RAGAS 모델 비교: gpt-5.6-luna vs gpt-4o-mini

실험일: 2026-10-19
코드 기준: 커밋 `9f32415`
관련 파일: `back/scripts/ragas_eval.py`, `back/app/services/rag.py`

## 1. 요약

운영 경로(`proposed`)의 LLM을 `gpt-5.6-luna`에서 `gpt-4o-mini`로 바꿔 RAGAS를 다시 돌렸습니다.

- **속도**: 답변 지연이 6.45초에서 2.98초로 절반 이하가 됩니다.
- **검색**: 4o-mini 재정렬기가 근거를 덜 걸러 근거 수가 2.76개에서 4.35개로 늘고, 검색 Precision이 0.715에서 0.409로 떨어집니다. 그래프 질문의 nDCG@10도 0.112 낮아집니다.
- **답변**: Answer Correctness가 0.046 낮아집니다. 95% 구간이 0을 조금 포함해 1회 실행으로는 유의하지 않습니다.
- **주의**: RAGAS Context Precision/Recall은 4o-mini에서 오히려 오릅니다. `LLM_MODEL` 하나가 재정렬·답변 생성·RAGAS 채점을 모두 정하므로, 이 상승은 4o-mini 채점이 관대하거나 근거가 많아진 영향일 가능성이 큽니다. 모델 품질 향상으로 읽으면 안 됩니다.

## 2. 실험 조건

| 항목 | 값 |
|---|---|
| 변형 | `proposed` (운영 경로) |
| 평가셋 | `paper/data/eval_set_v3.json` (`2026.10.17-v3`, 37건: 문서 17, 그래프 20) |
| 반복 | 모델별 r1 1회 |
| 재정렬·답변·채점 LLM | `gpt-5.6-luna` / `gpt-4o-mini` (`LLM_MODEL` 환경변수만 변경) |
| 검색 임베딩 / 채점 임베딩 | `text-embedding-3-small` / `text-embedding-3-large` |
| DB | `back/runtime/merged.db` |

논문 실험에 쓴 DB(`data/data_graph/daalgi.db`)는 현재 체크아웃에 없습니다. 남아 있는 DB 중 `merged.db`가 논문 스냅샷의 승인 링크 36개와 정답 문서 버전을 모두 포함하고, LLM 없이 도는 `hybrid` 검색을 재현했을 때 Recall 0.734(논문 0.741, 3회 모두 동일)로 가장 가까웠습니다. 완전히 같은 DB는 아니므로, 공정한 비교를 위해 luna도 같은 DB에서 다시 돌렸습니다. 표의 Δ는 같은 DB에서 돌린 두 실행의 차이입니다.

실행 명령 (`back/`에서):

```bash
DATABASE_URL="sqlite:///<절대경로>/back/runtime/merged.db" LLM_MODEL=gpt-4o-mini \
PYTHONPATH=. PYTHONIOENCODING=utf-8 uv run --extra hwp --extra eval python scripts/ragas_eval.py \
  --dataset ../paper/data/eval_set_v3.json --variant proposed --repeat-tag r1 \
  --run-id proposed_gpt-4o-mini_merged_r1 --output-dir runtime/paper-exp/proposed-gpt-4o-mini-merged
```

luna는 `LLM_MODEL=gpt-5.6-luna`와 run-id·출력 경로만 바꿔 실행했습니다.

## 3. 결과 (전체 37건)

Δ는 4o-mini − luna(같은 DB)이고, 괄호는 사례 단위 paired bootstrap 95% 구간입니다. 논문 luna는 `paper/experiments/results/proposed_r1–r3.json`의 평균으로, 참고용입니다.

| 지표 | 논문 luna | luna (같은 DB) | 4o-mini | Δ [95% CI] |
|---|---:|---:|---:|---|
| Faithfulness | 0.984 | 0.991 | 0.974 | −0.018 [−0.043, +0.004] |
| Answer Relevancy | 0.835 | 0.826 | 0.837 | +0.011 [−0.018, +0.040] |
| Answer Correctness | 0.797 | 0.810 | 0.764 | −0.046 [−0.103, +0.008] |
| Context Precision | 0.944 | 0.921 | 0.999 | +0.077 [+0.031, +0.131] |
| Context Recall | 0.955 | 0.966 | 1.000 | +0.034 [+0.014, +0.059] |
| 검색 Recall | 0.913 | 0.923 | 0.905 | −0.018 [−0.061, +0.020] |
| 검색 Precision | 0.699 | 0.715 | 0.409 | −0.306 [−0.416, −0.194] |
| MRR | 0.986 | 0.959 | 0.912 | −0.047 [−0.115, +0.014] |
| nDCG@10 | 0.914 | 0.908 | 0.844 | −0.063 [−0.114, −0.013] |
| 링크 정답 Recall | 0.708 | 0.725 | 0.700 | −0.025 [−0.075, +0.000] |
| 근거 수 | 2.73 | 2.76 | 4.35 | +1.60 [+0.89, +2.32] |
| 검색 지연(초) | 2.32 | 2.33 | 1.99 | −0.33 [−0.46, −0.21] |
| 답변 지연(초) | 6.14 | 6.45 | 2.98 | −3.47 [−4.10, −2.84] |

### 문서형 / 그래프형 분리

| 지표 | 문서 luna | 문서 4o-mini | 그래프 luna | 그래프 4o-mini |
|---|---:|---:|---:|---:|
| Faithfulness | 0.985 | 0.990 | 0.996 | 0.960 (Δ −0.036, 유의) |
| Answer Correctness | 0.855 | 0.822 | 0.771 | 0.715 |
| 검색 Precision | 0.650 | 0.420 | 0.771 | 0.401 |
| nDCG@10 | 0.979 | 0.974 | 0.847 | 0.734 (Δ −0.112, 유의) |
| 근거 수 | 2.59 | 3.18 | 2.90 | 5.35 |

품질 저하는 주로 그래프 질문에서 나타납니다. 4o-mini 재정렬기가 링크로 확장된 근거를 거의 걸러내지 못해 근거 수가 크게 늘고, 순위도 나빠집니다.

### 답변 생성 토큰 (37건 합계, 채점 호출 제외)

| 모델 | 입력 | 출력 |
|---|---:|---:|
| gpt-5.6-luna | 150,678 | 24,004 |
| gpt-4o-mini | 179,054 | 10,672 |

## 4. 한계와 다음 단계

- 모델별 1회 실행입니다. 같은 코드도 실행마다 ±0.02 정도 흔들립니다.
- 재정렬기·생성기·채점기가 함께 바뀌어 원인을 나눌 수 없습니다. 생성 효과만 보려면 채점 모델을 luna로 고정하고 재정렬·생성만 4o-mini로 바꿔야 합니다. 이를 위해서는 `ragas_eval.py`에 채점 모델 옵션을 따로 추가해야 합니다.
- 결과 원본(로컬, git 미포함): `back/runtime/paper-exp/proposed-gpt-4o-mini-merged/`, `back/runtime/paper-exp/proposed-gpt-5.6-luna-merged/`
