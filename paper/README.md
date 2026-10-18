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

- **완료:** Round 6 리뷰에 따라 기존 사례와 링크 기반 생성 사례를 나누고, 끝점 군집 기준으로 링크 확장과 H+RR·K3의 차이를 집계했다. 초록·본문의 기여와 표본 범위를 고치고 익명 DOCX·PDF를 갱신했다.
- **결과:** 그래프 질의 5건의 기존 사례와 링크를 먼저 골라 만든 15건의 신규 사례는 별도 보고한다. K3는 근거 수 최소치 기준선이며 고정된 출력·토큰 예산은 아니다. 신규 20건은 현업 전문가 1인이 비맹검 체크리스트로 검토해 모두 적합 판정을 받았지만, 독립 시험 자료를 뜻하지 않는다. 표의 군집 구간은 군집 수가 적어 기술적 민감도 결과로 해석한다.
- **다음:** 링크를 미리 고르지 않은 독립 질의셋, 두 명 이상의 독립 검수와 일치도, 출력 토큰을 맞춘 비교, 변형명을 가린 답변·근거 평가를 준비한다.
- **남은 사람 작업:** 링크 승인 기준과 문서 개정·폐기 절차를 확인한다. 과거 실행 시점의 링크 상태를 보존하고, 연결 근거가 없을 때 불완전 답변을 알리는 경고를 구현·검증한다.
- **운영 제한:** 독립 답변 평가와 누락 경고 검증이 끝나기 전에는 실제 운전 판단에 사용하지 않는다.

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
