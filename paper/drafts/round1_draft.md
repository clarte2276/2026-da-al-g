# 철도 운영 규정 질의응답을 위한 승인 링크 기반 선택적 Graph RAG

*Selective Graph RAG with Human-Approved Cross-Document Links for Railway Operation Regulation QA*

## 요약

철도 운전 질문은 일반 규정과 현장 길라잡이의 노선별 조치를 함께 요구한다.<br>
본 연구는 담당자가 승인한 문서 구간 링크를 최대 2 hop 확장하고 연결 근거만 질의별로 재정렬한다.<br>
신규 그래프형 15건에서 제안법의 검색 Precision/Recall은 0.800/0.889, Context Precision/Recall은 0.968/0.944였다.<br>
비교군은 부분 실행이고 신규 정답 라벨은 미검수이므로, 수치는 탐색적 결과로 한정한다.

## 1. 서론 및 관련 연구

운전원과 관제원이 설비 고장 대응을 확인할 때는 운전취급 규정의 일반 절차와 현장 길라잡이의 구체 조치를 함께 찾아야 한다. GraphRAG와 LightRAG는 문서에서 관계 그래프를 자동 구성하고, KG²RAG는 검색 seed에 연결된 문단을 그래프로 확장한다[3–5]. CARAG는 철도 운영·정비를 공간 지식 그래프로 다루지만[6], LegalBench-RAG의 전문가 근거 주석은 평가용 정답 구간이며 실행 시 확장하는 링크 그래프는 아니다[7]. 본 연구는 새 일반 그래프 검색 알고리즘보다, 담당자가 승인한 규정 조항–길라잡이 페이지 관계를 검색 경계로 관리하고 연결 근거를 질문별로 거르는 운영 설계를 다룬다.

## 2. 제안 방법

임베딩 유사도 0.6과 BM25 0.4를 결합해 후보를 찾고, 상위 20개를 재정렬해 직접 근거 5개를 선택한다. 직접 근거를 유지한 채 승인 링크를 최대 2 hop 따라가며, 링크 경유 근거만 다시 재정렬해 최대 10개를 답변 문맥에 추가한다. 선택 결과가 없거나 재정렬에 실패하면 연결 근거를 넣지 않는다. 답변은 문서 근거에 한정하고, 출력 인용은 근거와의 문자 겹침으로 보정한다.

![그림 1. 승인 링크 기반 검색 파이프라인](figures/fig1_pipeline.png)

그림 1. 직접 검색 근거를 보존하고 연결 근거만 선택하는 흐름.

## 3. 평가

평가셋 v3는 37건으로, 기존 v2 유래 17건(문서형 12, 그래프형 5)은 개발 자료로, 새 LLM 초안 20건(문서형 5, 그래프형 15)은 별도 집합으로 나눠 집계했다. 검색 정답은 문서 버전과 조항 번호 또는 페이지·슬라이드가 일치할 때 한 번만 센다. Precision은 최종 근거 수를 분모로 하며, 사례별 정답·검색 근거 수는 다르다. 검색은 `text-embedding-3-small`, 생성과 RAGAS 0.4.3 평가는 모두 `gpt-5.6-luna`, 평가 임베딩은 `text-embedding-3-large`를 사용했다. 생성 추론 강도는 medium이고 judge는 temperature 0으로 설정했다. 생성기와 judge가 같은 모델인 점은 편향 가능성을 남긴다. 코드 기준 커밋은 `2c2d5c6`이다.

표 1. 그래프형 검색 결과 (평균±반복 간 표본 표준편차)

| 집합·방법 | Precision | Recall | MRR |
|---|---:|---:|---:|
| 개발 제안법 | 0.57±0.04 | 0.69±0.04 | 1.00±0.00 |
| 신규 제안법 | 0.80±0.02 | 0.89±0.05 | 0.97±0.00 |
| 신규 link_all* | 0.78±0.04 | 0.92±0.02 | 1.00±0.00 |
| 신규 BM25† | 0.27 | 0.67 | 0.93 |

표 2. 그래프형 답변 및 문맥 결과

| 집합·방법 | CP | CR | AC |
|---|---:|---:|---:|
| 개발 제안법 | 0.79±0.07 | 0.83±0.02 | 0.74±0.03 |
| 신규 제안법 | 0.97±0.02 | 0.94±0.02 | 0.76±0.01 |
| 신규 link_all* | 0.95±0.04 | 0.95±0.01 | 0.77±0.03 |

모든 값은 반복별 사례 평균의 평균이며 ±는 반복 간 표본 표준편차다. 개발은 기존 그래프형 5건, 신규는 15건이다. CP/CR/AC는 Context Precision/Context Recall/Answer Correctness를 뜻한다. *`link_all` 신규 사례의 완료 수는 14, 15, 14건이다. †BM25는 검색 전용 r1이라 답변 지표가 없다. 제안법은 전체 37건을 3회 완료했으나 `link_all`은 31/37·35/37·31/37건이고 dense·hybrid·hybrid_rerank는 미실행이다.

전체 v3 그래프 20건의 제안법–`link_all` paired 비교에서 Context Precision 차이는 +0.0444였다(정확 Wilcoxon, p=0.0673, 짝 20건 중 비영 차이 14건). 전체 37건에서는 +0.0497이었다(p=0.0047, 짝 35건 중 비영 차이 20건). 각 p값은 3개 범주×9개 지표의 다중 비교 보정 전 탐색값이다. 20개 신규 사례의 라벨은 아직 사람 검수 전이며, 새 그래프 사례는 승인 링크 36개 중 서로 다른 15개만 사용했다. 전체 검색 지연은 제안법 2.323±0.030초, 부분 실행 `link_all` 1.816±0.054초였다.

## 4. 결론 및 한계

신규 사례에서 제안법은 `link_all`보다 Precision과 Context Precision이 높고 Recall과 Answer Correctness는 낮았으나, 비교군의 미완료 사례와 미검수 라벨 때문에 우월성으로 해석할 수 없다. 평가셋은 한 노선의 37문항이며 승인 링크 36개 중 15개만 시험했다. 라벨과 답변의 독립 전문가 검수, 동일 조건의 완결 기준선, 링크 변경·오류 및 현장 안전성 평가는 남아 있다. 따라서 기여는 철도 QA에서 승인 링크를 추적·선택하는 운영 방식에 한정된다.

## 참고문헌

[1] P. Lewis et al., “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” *NeurIPS*, vol. 33, pp. 9459–9474, 2020.

[2] W. Sun et al., “Is ChatGPT Good at Search? Investigating Large Language Models as Re-Ranking Agents,” *EMNLP*, pp. 14918–14937, 2023.

[3] D. Edge et al., “From Local to Global: A Graph RAG Approach to Query-Focused Summarization,” arXiv:2404.16130, 2024.

[4] X. Zhu et al., “Knowledge Graph-Guided Retrieval Augmented Generation,” *NAACL-HLT*, pp. 8912–8924, 2025.

[5] Z. Guo et al., “LightRAG: Simple and Fast Retrieval-Augmented Generation,” *Findings of EMNLP*, pp. 10746–10761, 2025.

[6] W. Zheng et al., “CARAG: Context-Aware Retrieval-Augmented Generation for Railway Operation and Maintenance Question Answering over Spatial Knowledge Graph,” *ISPRS International Journal of Geo-Information*, vol. 15, no. 2, Article 78, 2026.

[7] N. Pipitone and G. H. Alami, “LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain,” arXiv:2408.10343, 2024.

[8] S. Es et al., “RAGAs: Automated Evaluation of Retrieval Augmented Generation,” *EACL System Demonstrations*, pp. 150–158, 2024.
