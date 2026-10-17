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

- **완료:** Round 3 초안과 결과 요약을 갱신했다. 6개 검색 방식 모두 37건을 3회 완료했으며 새 실험이나 API 호출은 하지 않았다.
- **결과:** 그래프 질의에서 승인 링크 확장은 `hybrid_rerank` 대비 Recall과 링크 정답 Recall을 높였고, 선택 재정렬은 `link_all` 대비 Context Precision을 회복하면서 작은 Recall 감소를 보였다. 신규 라벨의 링크 구성 편향과 미검수 상태 때문에 결과는 탐색적으로 해석한다.
- **다음:** Round 4 교수 검토를 진행하고, 운영 규정 전문가 2명이 LLM 초안 20건의 질문·답·근거 위치를 독립 검수한다. 그래프 사례의 양쪽 링크 끝점 필요성과 불일치를 조정하고, 변형명을 가린 답변·근거의 사람 평가를 추가한다.
- **남은 사람 작업:** 승인 주체·기준·버전·폐기 절차와 평가 당시 링크 스냅샷을 확인한다. 링크 근거가 없을 때 불완전 답변을 알리는 경고를 구현·검증한다.
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
