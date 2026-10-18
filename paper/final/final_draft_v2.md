# 철도 규정 질의응답을 위한<br>승인 기반 교차문서 근거 검색

*Approval-Based Cross-Document Evidence Retrieval<br>for Railway Regulation Question Answering*

## 요약

철도 규정 질의에 정확하게 답변하기 위해 AI 시스템은 현장 길라잡이에 제시된 구체적인 조치 절차와 내부 규정의 보고·운전 조건을 함께 검색해야 한다. 본 연구는 관리자가 연결하고 승인한 문서 간 링크를 활용해 검색 결과를 확장하는 효과를 평가하고, 연결 근거의 선별 재정렬은 부차적으로 분석한다. 그래프형 질의에서 link_all과 hybrid_rerank_k3의 Recall 차이는 기존 사례에서 +0.128, 링크 기반 생성 사례에서 +0.267이다. 결과는 군집 단위 부트스트랩 신뢰구간과 함께 제시한다. 생성 사례 20건은 철도 운영기관 현업 전문가 1인의 체크리스트 검수를 거쳤다. 다만 생성 사례는 링크를 전제로 구성되었으므로 결과를 보수적으로 해석한다.

## 1. 서론 및 관련 연구

기관사와 관제원이 설비 고장 대응 절차를 확인하려면 현장 길라잡이의 구체적인 조치와 규정의 보고·운전 조건을 함께 찾아야 한다. 본 연구는 이러한 근거를 챗봇을 통해 확인하고 검토하는 과정을 지원하며, 운전 지시를 제공하거나 대체하지 않는다.

검색 증강 생성은 외부 근거를 답변 생성에 활용하며[1], LLM 기반 재정렬은 검색 후보를 질의 관련성에 따라 정렬한다[2]. GraphRAG와 LightRAG는 문서에서 관계 그래프를 구성하고[3,4], KG²RAG는 초기 검색 결과에서 연결된 청크를 확장한다[5]. 철도 QA 분야에서 CARAG는 개념·인스턴스 계층의 공간 지식그래프를 탐색하며, 도시철도 출입문 RAG는 고장 이력과 재정렬을 활용한다[6,7]. LegalBench-RAG는 전문가가 주석한 근거를 제공하고, 한국어 법률 RAG 연구는 검색 기법의 조합을 최적화한다[8,9]. 본 연구는 새로운 그래프 검색 알고리즘의 우월성보다, 관리자가 연결한 규정과 길라잡이의 문서 구간을 활용하는 검색 확장의 효과를 평가한다.

## 2. 방법

비교 방법은 BM25, Dense, Hybrid, H+RR (Hybrid 후보를 LLM이 재정렬하는 방식), K3, link_all, proposed의 7개로 구성한다. BM25는 어휘 일치 기반 검색, Dense는 임베딩 유사도 기반 검색이며, Hybrid는 두 검색 결과를 결합한다. 먼저 하이브리드 검색으로 후보 구간 20개를 찾고, LLM이 이 중 직접 근거를 최대 5개(top_k=5) 선택한다.

link_all과 proposed는 H+RR이 선택한 직접 근거를 보존하면서 승인 링크로 연결된 문서 구간을 추가한다. link_all은 최종 근거 수를 최대 15개(top_k×3)로 제한한다. proposed는 연결 근거만 질문 관련성에 따라 재정렬·선별하여 최대 10개(top_k×2)를 추가한다. K3(hybrid_rerank_k3)는 선택된 근거가 3개 미만이면 Hybrid 순위에 따라 보충하는 비교 방식으로, 근거 수에 따른 성능 변화를 살펴보기 위해 사용한다.

![그림 1. 승인 링크 기반 검색 과정](figures/fig1_pipeline.png)

그림 1. 승인 링크 기반 검색 과정. 직접 근거를 보존하고 연결 근거만 선별한다.

## 3. 평가 및 결과

평가셋은 기존 사례(existing_v2) 17건과 링크 기반 생성 사례(llm_drafted) 20건으로 구성된다. 기존 사례는 문서형 12건과 그래프형 5건, 생성 사례는 문서형 5건과 그래프형 15건이다. 생성 사례 20건은 철도 운영기관 현업 전문가 1인이 질문의 현실성, 정답 근거와 참조 답변의 정확성, 링크의 필요성을 체크리스트로 검토했다. 모두 적합 판정을 받았으며 수정·삭제된 사례는 없었다.

2절의 7개 방법으로 평가 질문 37건을 각각 3회 검색했다. hybrid_rerank_k3의 답변 생성과 RAGAS 평가[10]는 첫 번째 실행(r1)에서만 수행하고, r2와 r3에서는 검색만 평가했다. 따라서 검색 지표는 3회 평균이며, 이 기준선의 답변 지표와 동일 실행 간 답변 비교는 r1 결과이다. 답변 생성 모델과 자동 평가 모델은 모두 gpt-5.6-luna이다. 검색용 임베딩은 text-embedding-3-small, 평가용 임베딩은 text-embedding-3-large를 사용했다. 평가 시점의 승인 링크 스냅샷은 36개 행으로 구성되며, 해시는 재현용 기록에 보관했다. 승인 링크로 연결된 문서 구간 중 정답 근거로 지정한 구간을 링크 정답 근거라 한다. 평가 데이터에서는 이를 via_link로 표시한다.

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

표 2. 동일 질의에 대한 방법 간 차이와 끝점 군집 부트스트랩 95% 신뢰구간(10,000회). L=link_all, P=proposed, K3=hybrid_rerank_k3.

| 비교 | ΔRecall | Δ링크 정답 Recall |
|---|---:|---:|
| 기존 사례 (사례 5/군집 5) | | |
| L − K3 | +0.128<br>[+0.017, +0.244] | +0.367<br>[+0.067, +0.700] |
| P − K3 | +0.150<br>[+0.017, +0.283] | +0.400<br>[+0.100, +0.700] |
| P − L | +0.022<br>[+0.000, +0.067] | +0.033<br>[+0.000, +0.100] |
| 링크 기반 생성 사례 (사례 15/군집 6) | | |
| L − K3 | +0.267<br>[+0.083, +0.440] | +0.578<br>[+0.271, +0.889] |
| P − K3 | +0.244<br>[+0.098, +0.400] | +0.511<br>[+0.246, +0.806] |
| P − L | −0.022<br>[−0.083, +0.026] | −0.067<br>[−0.167, 0.000] |

동일한 정답 조항을 공유하는 사례 사이의 의존성을 고려해 군집 단위로 재표집했다. 같은 문서 버전과 조항을 via_link 정답 끝점으로 공유하는 사례들을 연결하고, 각 연결요소를 하나의 군집으로 정의했다. 링크 ID가 없어 끝점 공유 여부를 대리 지표로 사용했다. 기존 사례 5개 군집과 생성 사례 6개 군집은 규모가 작으므로 신뢰구간을 효과를 확정하는 근거로 사용하지 않는다. 생성 사례의 그래프형 질의 15건은 승인 링크와 양 끝의 원문에서 초안을 작성했으므로, 해당 링크를 전제로 구성된 표본이다.

표 3. proposed와 link_all의 출처별 문맥·답변·지연 차이 (proposed − link_all). 끝점 군집 부트스트랩 95% 신뢰구간을 제시한 탐색적 분석.

| 지표 | 기존 사례<br>(5/5) | 링크 기반<br>생성 사례 (15/6) |
|---|---:|---:|
| ΔContext<br>Precision | +0.109<br>[+0.002, +0.220] | +0.025<br>[+0.008, +0.042] |
| ΔAnswer<br>Correctness | −0.003<br>[−0.040, +0.042] | −0.001<br>[−0.019, +0.018] |
| Δ지연<br>(초/질의) | +1.057<br>[+0.904, +1.211] | +0.343<br>[−0.761, +1.066] |

proposed와 K3의 답변 지표는 동일한 첫 번째 실행(r1)에서 비교했다. 기존 사례의 Context Precision 차이는 −0.266 [−0.478, −0.099], Answer Correctness 차이는 −0.022 [−0.120, +0.077]이다. 생성 사례에서는 각각 +0.020 [−0.047, +0.078], +0.031 [−0.043, +0.136]이다. K3의 답변 평가와 이에 대응하는 비교는 단일 실행의 기술통계로만 해석한다.

그래프형 질의의 평균 지연은 K3, link_all, proposed 순으로 1.446초, 2.157초, 2.678초이다. 답변 생성과 자동 채점에는 같은 모델을 사용했으며, 블라인드 사람 평가는 수행하지 않았다. 비용은 일관되게 기록하지 않아 비교에서 제외했다.

## 4. 논의 및 결론

기존 사례와 링크 기반 생성 사례는 표본 구성 방식이 다르므로 출처별 결과와 신뢰구간을 나누어 해석해야 한다. K3는 선택된 근거가 부족할 때 최소 3개까지 보충하지만 근거 수를 고정하지 않는다. 따라서 이 비교는 예산 민감도 분석이며, 토큰 예산을 통제한 실험은 아니다. 평가 사례가 링크 활용에 유리한 질문에 치우쳤을 가능성이 있으므로, 본 결과만으로 실제 현장 질의 전반에서 동일한 효과를 기대하기는 어렵다.

스냅샷은 평가 시점의 링크 상태만 보존하며 과거 상태를 복원하지 못한다. 관리자는 링크 양 끝의 구간을 선택하고 승인 상태, 담당자, 시각을 기록한다. 다만 의미적 적합성에 대한 승인 기준과 문서 개정·폐기 시 링크 처리 규칙은 확인되지 않았다. 따라서 승인 상태를 독립적인 품질 검증 결과로 해석해서는 안 된다.

승인 링크 확장은 평가 사례의 교차문서 근거 회수를 도왔다. 이는 탐색적 결과이며, 링크 기반 생성 사례는 독립 검증 표본이 아니다. 링크 구조를 아는 전문가 1인이 검수했으며 평가자 간 일치도는 산출하지 못했다. 연결 근거가 누락되어도 시스템은 경고 없이 직접 근거만으로 답할 수 있으므로, 사람의 검수와 안전성 검증 전에는 실제 운전 판단에 사용해서는 안 된다.

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
