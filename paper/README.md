# 논문: 철도 운영 규정 질의응답을 위한 승인 링크 기반 선택적 Graph RAG

Selective Graph RAG with Human-Approved Cross-Document Links for Railway Operation Regulation QA
투고처: KIISE 학술대회 (본문 2~3쪽, 2단, 심사용 익명본)

## 구조


| 폴더                  | 내용                                                                     |
| ------------------- | ---------------------------------------------------------------------- |
| `references/forms/` | KIISE 양식 (심사용 `kiise_review_form.docx`, 출판용 `kiise_publish_form.docx`) |
| `references/`       | 선행 연구 정리, 참고문헌 목록                                                      |
| `data/`             | 평가셋 (질문, 참조 답변, 정답 근거 ID), 사람 검수 목록                                    |
| `experiments/`      | 실험 설정, 변형별·반복별 결과 JSON (`results/`), 집계 표 (`summary/`)                 |
| `drafts/`           | 라운드별 초안 `roundN_draft.md` / `roundN_draft.docx`                        |
| `reviews/`          | 라운드별 리뷰 `roundN/roundN_review_<리뷰어>.md`, 종합 `roundN/roundN_summary.md` |
| `final/`            | 최종본                                                                    |


실험 코드는 `back/`에 있습니다 (`back/app/services/rag.py`, `back/scripts/ragas_eval.py`).

## 진행 상황

- **완료:** Round 4 리뷰에 맞춰 근거 수 민감도 기준선, 출처별 paired 분석, 링크 끝점 군집 bootstrap, 평가 시점 링크 스냅샷과 프롬프트 식별자를 추가하고 초안·최종 DOCX를 갱신했다.
- **결과:** 그래프 결과는 `existing_v2` 개발 사례와 `llm_drafted` 링크 구성 사례를 나누어 보고한다. `hybrid_rerank_k3`는 reranker 선택이 3개 미만이면 hybrid 순위에서 보충하는 opt-in 기준선이며, 정확히 3개를 강제하지 않는다. 출처·군집별 표본이 작고 신규 gold가 미검수이므로 모든 차이는 탐색적으로 해석한다.
- **다음:** 운영 규정 전문가 2명이 LLM 초안 20건의 질문·답·근거 위치를 독립 검수한다. 그래프 사례의 양쪽 링크 끝점 필요성과 불일치를 조정하고, 변형명을 가린 답변·근거의 사람 평가를 추가한다.
- **남은 사람 작업:** 승인 기준·문서 개정 및 링크 폐기 절차를 확인한다. 링크 근거가 없을 때 불완전 답변을 알리는 경고를 구현·검증한다.
- **운영 제한:** 사람 검수, 링크 변경 이력 추적, 불완전 답변 경고 검증이 끝나기 전에는 실제 운전 판단에 사용하지 않는다.

## 평가 지표

### 1. 검색 품질 (gold 근거와 직접 대조, LLM 미사용)

| 지표 | 의미 |
|---|---|
| Recall | gold 근거 중 찾아낸 비율 |
| Precision | 찾아낸 근거 중 실제 gold인 비율 |
| MRR | 첫 번째 정답 근거가 얼마나 위에 나오는가 |
| nDCG@10 | 상위 10개 안에서 정답 근거가 위쪽에 잘 배치됐는가 |
| linked_gold_recall | 문서 간 질문에서, 승인 링크를 거쳐야만 닿는 gold 근거를 찾아낸 비율 (**제안 기법의 핵심 지표**) |
| special_rule_hit | 일반 규정보다 우선하는 특칙 문서의 근거가 포함됐는가 |

### 2. 답변 품질 (RAGAS, LLM 심판 채점)

| 지표 | 의미 |
|---|---|
| Faithfulness | 답변이 검색된 근거에만 기반하는가 (지어내지 않는가) |
| Answer Correctness | 참조 답변과 일치하는가 |
| Answer Relevancy | 질문에 맞는 답을 했는가 |
| Context Precision | 관련 근거가 상위에 배치됐는가 |
| Context Recall | 근거가 참조 답변에 필요한 내용을 다 담고 있는가 |
