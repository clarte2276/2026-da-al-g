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

- **완료:** Round 2 초안과 리뷰 요약을 갱신하고, 기존 평가 결과만 반영했다. 새 실험이나 API 호출은 하지 않았다.
- **보류:** LLM 초안 신규 20건의 질문·답·정답 라벨은 사람 검수가 필요하다. `link_all`은 반복별 14/15/14건만 완료됐고 `hybrid_rerank` 결과는 없다. 링크 승인·버전·폐기 기록은 저자 확인이 필요하며, API 크레딧 부족으로 전체 재실행도 대기 중이다.
- **다음:** 2명의 검토자가 신규 20건을 독립 검수하고, 크레딧 복구 후 6개 검색 방식(`bm25`, `dense`, `hybrid`, `hybrid_rerank`, `link_all`, `proposed`)을 37건·3회 반복으로 완주한다. 별도 사람 답변 검수와 링크 변경 이력 확인을 마치고, 링크 근거가 없을 때의 사용자 경고 기능을 구현·검증한다.
- **운영 제한:** 독립 검수와 안전 경고 검증이 끝나기 전에는 운영 판단에 사용하지 않는다.

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
