# 철도 규정 질의응답을 위한<br>승인 기반 교차문서 근거 검색

*Approval-Based Cross-Document Evidence Retrieval<br>for Railway Regulation Question Answering*

## 요약

철도 규정 질의에는 길라잡이의 조치 절차와 규정의 보고·운전 조건을 함께 확인할 필요가 있다. 본 연구는 관리자가 등록한 링크를 검색에 반영하는 link_all과 관련성이 높은 연결 근거를 선별하는 proposed를 평가했다. 기존 그래프 질의 5건과 링크 기반 신규 질의 15건에서 link_all의 K3 대비 Recall 차이는 각각 +0.128과 +0.267이었으나, 신규 질의는 평가 링크를 먼저 선택해 구성해 일반 현장 질의로 확대하기 어렵다.

## 1. 서론 및 관련 연구

설비 고장 절차를 확인하는 기관사와 관제원은 길라잡이의 조치와 규정의 보고·운전 조건을 함께 찾아야 한다. 본 연구는 근거 확인을 지원하며 운전 지시를 대신하지 않는다.

검색 증강 생성은 외부 근거를 활용하고[1], LLM 재정렬은 후보 순서를 조정한다[2]. GraphRAG·LightRAG·KG²RAG는 문서 관계와 검색 구간의 연결을 활용하며[3–5], CARAG는 철도 공간 지식그래프를, 도시철도 출입문 RAG는 고장 이력과 재정렬을 활용한다[6,7]. LegalBench-RAG와 한국어 법률 QA 연구도 도메인별 검색 근거를 다룬다[8,9]. 본 연구는 관리자 등록 링크를 이용한 철도 교차문서 검색에서 직접 근거를 보존하는 확장의 효과를 비교하고, 연결 근거 선별은 보조로 분석한다.

## 2. 방법

BM25는 어휘 일치도, Dense는 임베딩 유사도를 기준으로 검색하고 Hybrid는 두 검색 결과를 결합한다. H+RR은 Hybrid 후보 20개를 재정렬해 직접 근거를 최대 5개 선택한다.

link_all은 H+RR의 직접 근거에 승인 링크의 반대편 구간을 모두 더해 최대 15개를 구성한다. proposed는 관련성이 높은 연결 근거를 최대 10개 선별해 추가한다. K3는 선택 근거가 세 건보다 적으면 Hybrid 순위로 보충하는 최소 근거 수 기준선이다.

![그림 1. 승인 링크 기반 검색 과정](figures/fig1_pipeline.png)

그림 1. 직접 근거를 보존하고 연결 근거를 선별한다.

## 3. 평가 및 결과

평가 자료는 기존 사례 17건(문서형 12건, 그래프형 5건)과 링크 기반 생성 사례 20건(문서형 5건, 그래프형 15건)으로 구성했다. 신규 그래프 질의는 서로 다른 링크를 먼저 고른 다음 양쪽 문서에서 작성했으며, 검색 결과는 작성에 사용하지 않았다. 철도 운영기관 현업 전문가 1인이 신규 20건을 비맹검 체크리스트로 검토해 질문의 현실성, 정답 근거와 참조 답변의 정확성, 링크의 필요성을 확인했다. 20건 모두 적합 판정을 받아 수정하거나 삭제한 사례는 없었다.

각 방법은 37개 질의를 세 차례 검색했다. K3의 답변 평가는 첫 번째 실행(r1)에만 RAGAS[10]로 수행하고, 두 번째와 세 번째 실행(r2·r3)은 검색 성능 측정에 사용했다. 검색 지표는 세 차례 실행의 평균이며, K3의 답변 지표는 r1 결과만을 대상으로 비교했다. 생성과 자동 평가에는 gpt-5.6-luna를 사용했고, 검색 및 평가 임베딩에는 각각 text-embedding-3-small과 text-embedding-3-large를 사용했다. 평가에 사용한 승인 링크 36개는 2026년 10월 17일 상태로 스냅샷을 남겼으나, 실행 시점이 서로 달라 모든 실행에서 같은 링크 상태를 사용했는지는 확인하지 못했다. 링크를 통해 회수한 정답 구간은 링크 정답 근거로 별도 표시했다.

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

동일한 문서 버전과 조항을 링크 정답 끝점으로 공유하는 질의끼리 묶어 끝점 군집 단위로 재표집했다. 원자료에 링크 ID가 없어 끝점 공유 여부를 군집 기준으로 삼았다.

표 3. proposed와 link_all의 출처별 문맥·답변·지연 차이 (proposed − link_all). 끝점 군집 부트스트랩 95% 구간.

| 지표 | 기존 사례<br>(5/5) | 링크 기반<br>생성 사례 (15/6) |
|---|---:|---:|
| ΔContext<br>Precision | +0.109<br>[+0.002, +0.220] | +0.025<br>[+0.008, +0.042] |
| ΔAnswer<br>Correctness | −0.003<br>[−0.040, +0.042] | −0.001<br>[−0.019, +0.018] |
| Δ지연<br>(초/질의) | +1.057<br>[+0.904, +1.211] | +0.343<br>[−0.761, +1.066] |

proposed와 K3의 답변 지표는 첫 번째 실행(r1)의 결과끼리 비교했다. 기존 사례에서 Context Precision 차이는 −0.266 [−0.478, −0.099], Answer Correctness 차이는 −0.022 [−0.120, +0.077]이었다. 링크 기반 생성 사례에서는 두 지표의 차이가 각각 +0.020 [−0.047, +0.078], +0.031 [−0.043, +0.136]으로 나타났다.

그래프형 질의의 평균 지연은 K3 1.446초, link_all 2.157초, proposed 2.678초였다. 토큰 사용 기록이 일관되지 않아 비용은 비교하지 않았다.

## 4. 논의 및 결론

기존 그래프형 5건은 개발 자료이고, 평가 링크를 먼저 정해 작성한 신규 15건도 독립 현장 평가 자료가 아니다. 전문가 검토는 라벨 적합성 확인에 그쳤다. 끝점 군집도 5개와 6개뿐이므로 표의 구간은 효과 확정이 아닌 민감도 기술로 해석해야 한다.

link_all·proposed와 H+RR·K3의 비교는 검색 절차 전체를 대상으로 한다. 평균 근거 수(H+RR 2.08, K3 3.15, link_all 3.08, proposed 3.00건)가 달라 출력 수와 토큰 예산을 통제한 비교가 아니다. 승인 상태는 운영 메타데이터지만, 승인 기준과 문서 개정·폐기 절차는 확인하지 못했다.

링크 확장은 정답 근거 회수를 늘렸지만 승인 절차의 품질이나 현장 효용을 입증하지는 않는다. 블라인드 사람 평가는 없었고, 연결 근거가 없어도 경고 없이 답한다. 독립 답변 평가와 누락 경고 검증 전에는 운전 판단에 활용할 수 없다.

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
