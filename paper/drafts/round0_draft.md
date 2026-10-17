# 철도 운영 규정 질의응답을 위한 승인 링크 기반 선택적 Graph RAG

*Selective Graph RAG with Human-Approved Cross-Document Links for Railway Operation Regulation QA*

## 요약

철도 규정과 현장 길라잡이는 서로 다른 문서에 있어 노선별 특칙을 함께 찾아야 한다.<br>
본 연구는 담당자 승인 링크로 근거를 확장하고 연결 근거만 재정렬하는 Graph RAG를 제안한다.<br>
서울 6호선 평가셋은 규정형 17건과 그래프형 20건이며, 제안법은 3회 완전 실행했다.<br>
그래프형에서 제안법의 Precision/Recall은 0.742/0.839, Context Precision/Recall은 0.923/0.916이다.<br>
비교군 link_all은 부분 실행(회당 31–35/37건)으로, 그래프 Recall 0.853과 Answer Correctness 0.760을 보였다.<br>
관측된 정밀도 향상과 재현율 저하는 제한된 교집합 비교에 따른 탐색적 결과다.

## 1. 서론

운전취급 규정은 일반 절차를, 현장 길라잡이는 설비별 조치와 점검 순서를 설명한다. 두 문서가 분리되어 있으면 질의에 포함된 노선·상황 특칙이 일반 조항 검색에서 누락될 수 있다. 이를 보완하기 위해 본 연구는 (1) 담당자가 승인한 규정–길라잡이 구간 링크로 검색 범위를 확장하고, (2) 질문과 관련 있는 링크 경유 근거만 별도로 재정렬하며, (3) 문서형·그래프형 질의에서 검색 및 답변 지표를 비교한다.

## 2. 관련 연구

RAG는 외부 문서를 검색해 생성 답변의 근거로 사용한다[1]. LLM 재정렬은 초기 검색 결과의 질의 관련 순서를 조정한다[2]. GraphRAG 계열은 문서에서 관계를 자동 추출하거나 지식 그래프를 구성해 검색을 확장한다[3]. 규제 QA 벤치마크는 문장 수준 정답 근거의 중요성을 보였고[4], RAGAS는 문맥 정밀도·재현율과 답변 충실도 등 구성요소별 평가를 제공한다[5]. 본 연구는 자동 추출 그래프 대신 담당자가 승인한 교차 문서 링크를 경계로 사용하고, 링크의 존재만으로 근거를 채택하지 않도록 링크 경유 구간을 질의별로 재정렬한다.

## 3. 제안 방법

질의와 문서 단위의 임베딩 유사도(0.6), BM25(0.4)를 결합하고, 상위 20개 후보를 LLM으로 재정렬해 직접 근거(top_k=5)를 얻는다. 직접 근거에서 승인 링크를 최대 2 hop까지 확장한다. 직접 근거는 유지하고 링크 경유 근거만 다시 재정렬하여 최대 2×top_k개를 선택한다. 재정렬이 실패하거나 선택 결과가 없으면 링크 근거는 제외한다. 답변 뒤에는 잘못된 근거 번호를 제거하고 문장과 실제 근거의 겹침을 이용해 인용을 보정한다.

![그림 1. 승인 링크 기반 선택적 검색 파이프라인](figures/fig1_pipeline.png)

그림 1. 하이브리드 검색, 직접·연결 근거 재정렬, 인용 보정 흐름.

## 4. 실험

평가셋은 37건(규정형 17, 그래프형 20)이다. 신규 작성된 20건의 정답과 근거 라벨은 LLM 초안으로, 사람 검수 전이다. BM25는 검색 전용 1회, 제안법은 전체 답변 평가 3회, link_all은 체크포인트 3회(31, 35, 31건)만 있다. Dense, hybrid, hybrid_rerank는 미실행이다. 검색 지표는 문서 조각 단위 정답 근거의 Precision, Recall, MRR이며, 답변 평가는 RAGAS의 Context Precision/Recall과 Answer Correctness를 사용했다. 표는 그래프형 지표의 반복별 사례 평균을 다시 평균한 값±표본 표준편차(평균 소수점 3자리, 표준편차 2자리)다. 1회 실행은 표준편차를 계산하지 않았다.

표 1. 그래프형 검색 성능

| 변형 | Precision | Recall | MRR |
|---|---|---|---|
| BM25 (r1) | 0.250 | 0.575 | 0.817 |
| Dense | TODO(실험 미완료) | TODO(실험 미완료) | TODO(실험 미완료) |
| Hybrid | TODO(실험 미완료) | TODO(실험 미완료) | TODO(실험 미완료) |
| Hybrid rerank | TODO(실험 미완료) | TODO(실험 미완료) | TODO(실험 미완료) |
| Link all (partial, n=19–20/20) | 0.737±0.02 | 0.853±0.02 | 0.965±0.02 |
| 제안법 (3회) | 0.742±0.02 | 0.839±0.05 | 0.975±0.00 |

표 2. 그래프형 답변 및 문맥 평가(Context Precision/Recall, Answer Correctness)

| 변형 | Context Precision | Context Recall | Answer Corr. |
|---|---|---|---|
| BM25 | TODO(실험 미완료) | TODO(실험 미완료) | TODO(실험 미완료) |
| Dense | TODO(실험 미완료) | TODO(실험 미완료) | TODO(실험 미완료) |
| Hybrid | TODO(실험 미완료) | TODO(실험 미완료) | TODO(실험 미완료) |
| Hybrid rerank | TODO(실험 미완료) | TODO(실험 미완료) | TODO(실험 미완료) |
| Link all (partial, n=19–20/20) | 0.883±0.01 | 0.936±0.01 | 0.760±0.03 |
| 제안법 (3회) | 0.923±0.03 | 0.916±0.01 | 0.756±0.01 |

전체 사례에서 제안법의 Recall/Context Precision/Answer Correctness는 0.913/0.944/0.797, link_all은 0.912/0.887/0.788이다(부분 자료). 사례명 교집합 비교에서 그래프형 제안법의 Precision 차이는 +0.018, Recall −0.019(n=20), Context Precision +0.044(p=0.067), Answer Correctness −0.004였다. 전체 사례 교집합의 Context Precision 차이는 +0.050(p=0.0047, n=35)였다. 양측 exact Wilcoxon 검정은 사례별 반복 평균을 비교했다. 그래프형 Recall이 낮은 사례(`graph_single_cm_failure`, `guide_atc`의 반복 평균 0.50)도 있어 개선 효과를 일반화할 수 없다. 부분 실행 비교 결과는 탐색적으로 해석한다.

## 5. 결론 및 한계

승인 링크 경유 근거의 선택 재정렬은 전체 사례에서 비교군보다 높은 Context Precision과 비슷한 Recall을 보였으나, 그래프형에서는 Recall과 Answer Correctness가 낮았다. 이는 정밀도–재현율 간 절충 가능성을 보일 뿐 우월성을 입증하지 않는다. 평가셋 37건 중 신규 20건은 LLM 초안 라벨로 사람 검수가 남아 있고, 답변 평가도 같은 계열 LLM judge에 의존한다. 단일 철도 문서 도메인, 작은 표본, link_all 부분 실행, 미실행 변형이 한계이며 추가 검수와 반복 실험이 필요하다.

## 참고문헌

[1] P. Lewis et al., “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” Advances in Neural Information Processing Systems, vol. 33, pp. 9459–9474, 2020.

[2] W. Sun et al., “Is ChatGPT Good at Search? Investigating Large Language Models as Re-Ranking Agents,” Proceedings of EMNLP, pp. 14918–14937, 2023.

[3] D. Edge et al., “From Local to Global: A Graph RAG Approach to Query-Focused Summarization,” arXiv:2404.16130, 2024.

[4] N. Pipitone and G. H. Alami, “LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain,” arXiv:2408.10343, 2024.

[5] S. Es et al., “RAGAs: Automated Evaluation of Retrieval Augmented Generation,” Proceedings of EACL 2024: System Demonstrations, pp. 150–158, 2024.
