# 논문: 철도 운영 규정 질의응답을 위한 승인 링크 기반 선택적 Graph RAG

Selective Graph RAG with Human-Approved Cross-Document Links for Railway Operation Regulation QA
투고처: KIISE 학술대회 (본문 2~3쪽, 2단, 심사용 익명본)

## 구조

| 폴더 | 내용 |
|---|---|
| `references/forms/` | KIISE 양식 (심사용 `kiise_review_form.docx`, 출판용 `kiise_publish_form.docx`) |
| `references/` | 선행 연구 정리, 참고문헌 목록 |
| `data/` | 평가셋 (질문, 참조 답변, 정답 근거 ID), 사람 검수 목록 |
| `experiments/` | 실험 설정, 변형별·반복별 결과 JSON (`results/`), 집계 표 (`summary/`) |
| `drafts/` | 라운드별 초안 `roundN_draft.md` / `roundN_draft.docx` |
| `reviews/` | 라운드별 리뷰 `roundN/roundN_review_<리뷰어>.md`, 종합 `roundN/roundN_summary.md` |
| `final/` | 최종본 |

실험 코드는 `back/`에 있습니다 (`back/app/services/rag.py`, `back/scripts/ragas_eval.py`).
