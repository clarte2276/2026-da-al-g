# 철도 규정 질의응답을 위한<br>승인 기반 교차문서 근거 검색

*Approval-Based Cross-Document Evidence Retrieval<br>for Railway Regulation Question Answering*

## 요약

철도 규정 질의에는 길라잡이의 조치 절차와 규정의 보고·운전 조건이 함께 필요하다. 본 연구는 관리자 등록 링크로 검색 근거를 확장하고 연결 근거를 선별하는 절차를 평가한다. 그래프 질의에서 링크를 모두 추가한 방식과 K3의 Recall 차이는 기존 5건에서 +0.128, 링크 기반 생성 15건에서 +0.267이었다. 현업 전문가 1인이 신규 20건을 비맹검 체크리스트로 검토했다. 신규 그래프 질의는 평가 링크에서 작성됐으며 K3는 최소 근거 수 기준선이다.

## 1. 서론 및 관련 연구

기관사와 관제원이 설비 고장 절차를 확인할 때는 길라잡이의 조치와 규정의 보고·운전 조건을 함께 찾아야 한다. 본 연구는 근거 확인을 돕되 운전 지시를 대신하지 않는다.

검색 증강 생성은 외부 근거를 쓰고[1], LLM 재정렬은 후보 순서를 조정한다[2]. GraphRAG·LightRAG·KG²RAG는 문서 관계와 검색 구간의 연결을 활용한다[3–5]. CARAG는 철도 공간 지식그래프를, 도시철도 출입문 RAG는 고장 이력과 재정렬을 쓴다[6,7]. LegalBench-RAG와 한국어 법률 QA 연구도 도메인별 검색 근거를 다룬다[8,9]. 본 연구는 관리자 등록 링크를 이용한 철도 교차문서 검색의 근거 회수를 비교한다. 직접 근거를 보존하는 확장이 중심이며 연결 근거 선별은 보조 분석이다.

## 2. 방법

BM25, Dense, Hybrid, H+RR, K3, `link_all`, `proposed`를 비교했다. BM25는 어휘, Dense는 임베딩, Hybrid는 두 검색 결과를 쓴다. H+RR은 하이브리드 후보 20개 중 직접 근거를 최대 5개 고른다.

`link_all`과 `proposed`는 H+RR의 직접 근거에 DB상 승인 링크의 반대편 구간을 더한다. `link_all`은 전체 근거를 최대 15개, `proposed`는 관련성 순으로 고른 연결 근거를 최대 10개 추가한다. K3는 선택 근거가 세 건보다 적을 때 Hybrid 순위로 채우는 기준선이다. 출력 수와 토큰 예산은 고정하지 않는다.

![그림 1. 승인 링크 기반 검색 과정](figures/fig1_pipeline.png)

그림 1. 직접 근거를 보존하고 연결 근거를 선별한다.

## 3. 평가 및 결과

평가 자료는 기존 사례 17건(문서형 12건, 그래프형 5건)과 링크 기반 생성 사례 20건(문서형 5건, 그래프형 15건)이다. 신규 그래프 질의는 서로 다른 링크를 먼저 고른 뒤 양쪽 문서에서 작성했고 검색 결과는 사용하지 않았다. 철도 운영기관 현업 전문가 1인이 신규 20건을 비맹검 체크리스트로 검토했다. 질문 현실성, 정답 근거와 참조 답변의 정확성, 링크 필요성을 확인했으며 모두 적합 판정을 받았다(수정·삭제 0건).

각 방법은 37개 질의를 세 차례 검색했다. K3는 첫 실행(r1)에만 RAGAS 답변 평가[10]를 했고, r2·r3는 검색만 수행했다. 검색 값은 3회 평균, K3 답변 비교는 r1끼리다. 생성기와 자동 평가기는 `gpt-5.6-luna`이며 검색·평가 임베딩은 `text-embedding-3-small`·`text-embedding-3-large`다. 2026-10-17 링크 스냅샷은 36행이고 SHA-256은 `07ccf6483a38d65229023a5fada5edbea7794d016bba03d544252b408fbc43ea`다(`paper/data/link_snapshot_20261017.json`; 기록은 `paper/experiments/provenance.md`). `proposed` r1–r3는 10월 16일 17:02–17:07 UTC, `link_all` r1은 10월 17일 01:09 UTC, K3 r1은 05:02 UTC에 실행됐다. 집계표와 코드는 `paper/experiments/summary/main_table.md`, `paper/experiments/aggregate.py`에 있다. 링크를 거쳐 찾는 정답 구간은 링크 정답 근거로 표시했다.

표 1. 그래프형 질의의 검색 결과(n=20). 3회 반복 평균±표준편차. H+RR=hybrid_rerank, K3=hybrid_rerank_k3.

| 변형 | Recall | 링크 정답<br>Recall | 근거 수<br>/질의 |
|---|---:|---:|---:|
| BM25 | 0.592±.000 | 0.275±.000 | 5.00±.00 |
| Dense | 0.383±.000 | 0.000±.000 | 5.00±.00 |
| Hybrid | 0.521±.000 | 0.150±.000 | 5.00±.00 |
| H+RR | 0.586±.019 | 0.233±.014 | 2.08±.06 |
| K3 | 0.618±.017 | 0.225±.043 | 3.15±.05 |
| link_all | 0.850±.014 | 0.750±.000 | 3.08±.03 |
| proposed | 0.839±.046 | 0.708±.063 | 3.00±.17 |

표 2. 방법 간 Recall 차이와 링크 정답 Recall 차이. 대괄호는 끝점 군집 부트스트랩 95% 기술 민감도 구간(10,000회). H+RR=hybrid_rerank, L=link_all, P=proposed, K3=hybrid_rerank_k3.

| 비교 | ΔRecall | Δ링크 정답 Recall |
|---|---:|---:|
| 기존 사례 (사례 5/군집 5) | | |
| L − H+RR | +0.189<br>[+0.072, +0.283] | +0.333<br>[+0.033, +0.700] |
| P − H+RR | +0.211<br>[+0.100, +0.294] | +0.367<br>[+0.067, +0.700] |
| L − K3 | +0.128<br>[+0.017, +0.244] | +0.367<br>[+0.067, +0.700] |
| P − K3 | +0.150<br>[+0.017, +0.283] | +0.400<br>[+0.100, +0.700] |
| P − L | +0.022<br>[+0.000, +0.067] | +0.033<br>[+0.000, +0.100] |
| 링크 기반 생성 사례 (사례 15/군집 6) | | |
| L − H+RR | +0.289<br>[+0.115, +0.462] | +0.578<br>[+0.286, +0.881] |
| P − H+RR | +0.267<br>[+0.133, +0.417] | +0.511<br>[+0.250, +0.800] |
| L − K3 | +0.267<br>[+0.083, +0.440] | +0.578<br>[+0.271, +0.889] |
| P − K3 | +0.244<br>[+0.098, +0.400] | +0.511<br>[+0.246, +0.806] |
| P − L | −0.022<br>[−0.083, +0.026] | −0.067<br>[−0.167, 0.000] |

같은 문서 버전과 조항을 링크 정답 끝점으로 공유하는 질의를 묶어 재표집했다. 데이터에 링크 ID가 없어 끝점 공유로 군집을 정했다. 집계표에는 반복별 사례 점수, 비교별 구간과 계산 절차를 기록했다(`paper/experiments/summary/main_table.md`).

표 3. proposed와 link_all의 출처별 문맥·답변·지연 차이 (proposed − link_all). 끝점 군집 부트스트랩 95% 구간.

| 지표 | 기존 사례<br>(5/5) | 링크 기반<br>생성 사례 (15/6) |
|---|---:|---:|
| ΔContext<br>Precision | +0.109<br>[+0.002, +0.220] | +0.025<br>[+0.008, +0.042] |
| ΔAnswer<br>Correctness | −0.003<br>[−0.040, +0.042] | −0.001<br>[−0.019, +0.018] |
| Δ지연<br>(초/질의) | +1.057<br>[+0.904, +1.211] | +0.343<br>[−0.761, +1.066] |

연결 근거 선별 방식과 K3의 답변 지표는 r1끼리 비교했다. 기존 사례의 Context Precision 차이는 −0.266 [−0.478, −0.099], Answer Correctness는 −0.022 [−0.120, +0.077]이다. 생성 사례에서는 각각 +0.020 [−0.047, +0.078], +0.031 [−0.043, +0.136]이다. 표 2·3은 연결 근거 선별과 전체 링크 추가의 차이도 보고한다.

그래프 질의의 평균 지연은 K3 1.446초, 전체 링크 추가 방식 2.157초, 연결 근거 선별 방식 2.678초다. 비용은 일관된 토큰 기록이 없어 비교하지 않았다.

## 4. 논의 및 결론

기존 그래프 5건은 개발 자료이고 신규 15건은 평가 링크를 먼저 정해 만들었다. 전문가 1인의 비맹검 검토는 라벨 확인이지 독립 현장 검증은 아니다. 군집은 각각 5개와 6개뿐이어서 구간은 민감도 기술에 그친다.

전체 링크 추가·연결 근거 선별 방식과 H+RR·K3의 차이는 검색 절차 전체를 비교한다. K3는 세 건을 최소치로 채우며 출력 수·토큰 예산은 맞추지 않았다(평균 근거 수: H+RR 2.08, K3 3.15, 전체 링크 추가 3.08, 연결 근거 선별 3.00). 승인 상태는 운영 메타데이터다. 승인 기준과 문서 개정·폐기 절차는 확인되지 않았다. 10월 17일 스냅샷은 과거를 복원하지 못하고 실행일도 달라 공통 링크 상태를 확인할 수 없다.

이번 사례에서 링크 확장은 더 많은 정답 근거를 찾았지만 승인 자체의 품질이나 현장 효용을 입증하지 않는다. 답변 생성기와 자동 평가기는 같은 모델을 썼고 블라인드 사람 평가는 없었다. 연결 근거가 없어도 경고 없이 답하므로, 독립 답변 평가와 누락 경고 검증 전에는 운전 판단에 사용하지 않는다.

## 참고문헌

[1] P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Küttler, M. Lewis, W. Yih, T. Rocktäschel, S. Riedel, and D. Kiela, “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” *Advances in Neural Information Processing Systems*, vol. 33, pp. 9459–9474, 2020.

[2] W. Sun, L. Yan, X. Ma, S. Wang, P. Ren, Z. Chen, D. Yin, and Z. Ren, “Is ChatGPT Good at Search? Investigating Large Language Models as Re-Ranking Agents,” in *Proceedings of EMNLP 2023*, pp. 14918–14937, 2023.

[3] D. Edge, H. Trinh, N. Cheng, J. Bradley, A. Chao, A. Mody, S. Truitt, D. Metropolitansky, R. O. Ness, and J. Larson, “From Local to Global: A Graph RAG Approach to Query-Focused Summarization,” arXiv:2404.16130, 2024.

[4] Z. Guo, L. Xia, Y. Yu, T. Ao, and C. Huang, “LightRAG: Simple and Fast Retrieval-Augmented Generation,” in *Findings of EMNLP 2025*, pp. 10746–10761, 2025.

[5] X. Zhu, Y. Xie, Y. Liu, Y. Li, and W. Hu, “Knowledge Graph-Guided Retrieval Augmented Generation,” in *Proceedings of NAACL 2025: Human Language Technologies*, vol. 1, pp. 8912–8924, 2025.

[6] W. Zheng, M. Yang, Y. Ren, H. Wang, C. Zeng, and Y. Zhang, “CARAG: Context-Aware Retrieval-Augmented Generation for Railway Operation and Maintenance Question Answering over Spatial Knowledge Graph,” *ISPRS International Journal of Geo-Information*, vol. 15, no. 2, Article 78, 2026.

[7] L. Huang, Z. Liu, C. Yu, T. Zhu, and B. Yan, “Emergency Operation Scheme Generation for Urban Rail Transit Train Door Systems Using Retrieval-Augmented Large Language Models,” *Sensors*, vol. 26, no. 6, Article 2006, 2026.

[8] N. Pipitone and G. H. Alami, “LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain,” arXiv:2408.10343, 2024.

[9] 서준원, 민정혜, “한국어 법률 QA를 위한 하이브리드 RAG 시스템 최적화,” *한국컴퓨터정보학회논문지*, 제30권, 제8호, pp. 53–63, 2025.

[10] S. Es, J. James, L. Espinosa Anke, and S. Schockaert, “RAGAs: Automated Evaluation of Retrieval Augmented Generation,” in *Proceedings of EACL 2024: System Demonstrations*, pp. 150–158, 2024.
