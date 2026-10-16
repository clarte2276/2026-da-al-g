# 철도 운영 규정 질의응답을 위한 승인 링크 기반 선택적 Graph RAG

*Selective Graph RAG with Human-Approved Cross-Document Links for Railway Operation Regulation QA*

## 요약

철도 운전 질문에는 일반 규정과 현장 길라잡이의 노선별 조치가 함께 필요하다.<br>
본 연구는 관리자 승인 문서 구간 링크를 따라 근거를 확장하고 연결 근거만 질문별로 다시 고르는 Graph RAG 운영 설계를 다룬다.<br>
신규 그래프 사례 15건에서 제안법의 검색 Precision/Recall은 0.800/0.889, Context Precision/Recall은 0.968/0.944였다.<br>
신규 정답 라벨은 미검수이고 비교군도 부분 실행이므로 이 수치는 탐색 결과이며, 성능 우월성이나 현장 안전성의 근거가 아니다.

## 1. 서론 및 관련 연구

기관사와 관제원이 설비 고장 대응을 확인할 때는 길라잡이의 구체 조치와 규정의 보고·운전 조건을 함께 찾아야 한다. 예를 들어 보조전원장치 기동불능 질의는 연장급전·부하감소 절차와 관제 보고 의무를 함께 확인한다. 본 연구의 범위는 오프라인 근거 확인·검토 지원이며, 운전 지시를 제공하거나 대체하지 않는다.

검색 증강 생성은 외부 근거를 답변에 연결하고[1], LLM 재정렬은 검색 후보의 질의 관련 순서를 조정한다[2]. GraphRAG와 LightRAG는 문서에서 관계 그래프를 구성하며[3,4], KG²RAG는 검색 seed와 연결된 문단을 그래프로 확장한다[5]. 철도 QA의 CARAG는 공간·사례 지식 그래프를 탐색하고, 도시철도 출입문 RAG는 고장 이력·하이브리드 검색·재정렬을 이용한다[6,7]. LegalBench-RAG는 평가용 전문가 근거 구간을 제공하고[8], 한국어 법률 하이브리드 RAG는 검색 조합을 최적화한다[9]. 이 연구들은 각각 그래프 구성, 검색 확장, 평가 주석을 다룬다. 본 연구는 새 검색 알고리즘의 우월성을 주장하지 않고, 관리자가 승인한 규정–길라잡이 구간 링크를 확장 경계로 삼아 링크 유래 근거만 질문별로 선택하는 운영 설계에 한정한다.

## 2. 제안 방법

하이브리드 검색과 1차 재정렬로 직접 근거를 고른 뒤, 직접 근거는 보존하고 승인 링크를 따라 연결 구간을 가져온다. 연결 구간만 다시 재정렬해 답변 문맥에 추가하며, 선택 결과가 없거나 재정렬이 실패하면 연결 근거를 넣지 않는다. 이때 직접 근거만으로 답변이 생성될 수 있어 필요한 특칙이 빠질 수 있다. 연결 링크는 관리자 승인 상태로 조회하지만, 승인 기준·담당자·폐기 기록 및 실행 시 링크 스냅샷은 이 평가 자료에서 추적되지 않는다.

![그림 1. 승인 링크 기반 검색 파이프라인](figures/fig1_pipeline.png)

그림 1. 직접 근거를 유지하고 링크 경유 근거만 선택한다.

## 3. 평가

평가셋 v3의 기존 사례 17건은 개발 자료로 분리하고, LLM 초안 신규 사례 20건은 별도 집계했다. 아래 그래프 지표는 기존 그래프 사례 5건과 신규 그래프 사례 15건의 결과를 나눠 보인다. 신규 사례는 서로 다른 승인 링크를 하나씩 골라 양쪽 원문으로 작성했으며, 검색 결과를 보고 고르지는 않았다. 검색 정답은 문서 버전과 조항 또는 페이지·슬라이드가 일치할 때 한 번만 센다. Precision의 분모는 최종 근거 수다. 답변 지표는 RAGAS 자동 평가이며[10], 생성·평가 judge는 `gpt-5.6-luna`, 검색 임베딩은 `text-embedding-3-small`, 평가 임베딩은 `text-embedding-3-large`를 사용했다. 같은 생성 모델과 judge에 의존하므로 독립 검증으로 보지 않는다.

표 1. 그래프형 검색 결과 (반복별 사례 평균의 평균 ± 반복 간 표본 표준편차)

| 집합·방법 | Precision | Recall | MRR |
|---|---:|---:|---:|
| 개발 제안법 | 0.57±0.04 | 0.69±0.04 | 1.00±0.00 |
| 신규 제안법 | 0.80±0.02 | 0.89±0.05 | 0.97±0.00 |
| 신규 link_all* | 0.78±0.04 | 0.92±0.02 | 1.00±0.00 |

표 2. 그래프형 문맥·답변 결과

| 집합·방법 | CP | CR | AC |
|---|---:|---:|---:|
| 개발 제안법 | 0.79±0.07 | 0.83±0.02 | 0.74±0.03 |
| 신규 제안법 | 0.97±0.02 | 0.94±0.02 | 0.76±0.01 |
| 신규 link_all* | 0.95±0.04 | 0.95±0.01 | 0.77±0.03 |

개발 결과는 기존 그래프 사례 5건, 신규 결과는 15건이다. CP/CR/AC는 Context Precision/Context Recall/Answer Correctness를 뜻한다. 제안법은 신규 사례를 반복마다 모두 완료했지만 `link_all`은 반복별 14·15·14건만 완료했다*. 사례별 점수는 가용 반복 평균으로 짝지었다. 신규 15건의 제안법−`link_all` 평균 차이는 Precision +0.0411(15쌍 중 비영 차이 7), Recall −0.0333(15쌍 중 4), Context Precision +0.0231(15쌍 중 9; 양측 exact Wilcoxon p=0.1289)이다. p값은 2개 소스 그룹·9개 지표 비교에서 보정하지 않은 탐색값이며, 반복 수가 불균형하고 일부 문항이 같은 규정·링크를 공유한다. *`link_all` 수치는 부분 실행 자료다. 신규 라벨은 아직 사람 검수 전이며, 서로 다른 승인 링크 36개 중 15개만 사용했다. 신규 그래프 검색 지연은 제안법 2.638±0.030초, 부분 실행 `link_all` 1.689±0.030초다. 토큰 비용은 집계되지 않아 비용 비교로 해석할 수 없다.

## 4. 결론 및 한계

이 결과는 미검수 신규 사례에서의 제한된 파이프라인 점검이다. 자동 judge는 생성 모델과 같고, 신규 질문·답·근거 및 링크 양끝의 필요성은 독립 검증되지 않았다. `link_all`의 누락 사례와 반복 수 불균형, 미실행 `hybrid_rerank` 비교도 선택 재정렬의 효과를 분리하지 못한다. 운영 사용 전에 규정 실무자의 독립 검수, 동일 조건의 완결 기준선, 링크 승인·버전·폐기 절차의 추적이 필요하다. 현재 시스템은 연결 근거가 선택되지 않아도 직접 근거로 답할 수 있고 이를 알리는 별도 경고가 없다. 따라서 안전성 검증 전에는 실제 운전 판단에 사용해서는 안 되며, 사용자 경고 기능도 구현·검증이 필요하다.

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

[10] S. Es, J. James, L. Espinosa Anke, and S. Schockaert, “RAGAs: Automated Evaluation of Retrieval Augmented Generation,” in *Proceedings of EACL 2024: System Demonstrations*, pp. 150–58, 2024.
