# 사람 승인 교차문서 링크를 이용한 철도 규정 근거 검색 향상

*Improving Evidence Retrieval for Railway Regulation QA with Human-Approved Cross-Document Links*

## 요약

철도 규정 질의는 일반 규정과 현장 길라잡이의 노선별 조치를 함께 요구할 수 있다.<br>
본 연구는 사람이 승인한 교차문서 구간 링크를 검색 확장 경계로 평가하고, 링크 근거만 다시 고르는 선택 재정렬을 부차 기여로 분석한다.<br>
그래프 질의 20건에서 링크 기반 두 방식은 `hybrid_rerank`보다 Recall을 0.253–0.264, 링크 정답 Recall을 0.475–0.517 높였다.<br>
다만 20건 중 15건은 해당 링크에서 LLM이 초안한 미검수 사례이므로, 결과는 탐색적 파이프라인 평가로 한정한다.

## 1. 서론 및 관련 연구

기관사와 관제원이 설비 고장 대응을 확인할 때는 길라잡이의 구체 조치와 규정의 보고·운전 조건을 함께 찾아야 한다. 예를 들어 보조전원장치 기동불능 질의에는 연장급전·부하감소 절차와 관제 보고 의무가 모두 필요할 수 있다. 본 연구가 다루는 범위는 오프라인 근거 확인·검토 지원이며, 운전 지시를 제공하거나 대체하지 않는다.

검색 증강 생성은 외부 근거를 답변에 연결하고[1], LLM 재정렬은 검색 후보의 질의 관련 순서를 조정한다[2]. GraphRAG와 LightRAG는 문서에서 관계 그래프를 구성하며[3,4], KG²RAG는 검색 seed와 연결된 문단을 확장한다[5]. 철도 QA의 CARAG는 공간·사례 그래프를 탐색하고, 도시철도 출입문 RAG는 고장 이력과 재정렬을 이용한다[6,7]. LegalBench-RAG는 평가용 전문가 근거 주석을 제공하며[8], 한국어 법률 하이브리드 RAG는 검색 조합을 최적화한다[9]. 본 연구는 새 검색 알고리즘의 우월성을 주장하지 않고, 사람이 승인한 규정–길라잡이 구간 링크를 확장 경계로 삼는 운영 설계를 평가한다.

## 2. 방법

하이브리드 검색과 1차 재정렬로 직접 근거를 고른 뒤, 직접 근거는 보존하고 승인 링크로 연결 구간을 확장한다. `link_all`은 연결 근거를 모두 포함하고, `proposed`는 그 연결 근거만 질문별로 다시 재정렬해 선택한다. 선택 결과가 없거나 재정렬에 실패하면 연결 근거를 넣지 않으므로 직접 근거만으로 답변할 수 있다.

![그림 1. 승인 링크 기반 검색 파이프라인](figures/fig1_pipeline.png)

그림 1. 직접 근거를 유지하고 링크 경유 근거만 선택한다.

## 3. 평가 및 결과

평가셋 v3의 `existing_v2` 17건(문서형 12, 그래프형 5)은 개발 자료로, `llm_drafted` 20건(문서형 5, 그래프형 15)은 별도로 보고했다. 6개 변형을 모두 37건에서 3회 완주했다. 표의 값은 반복별 사례 평균의 평균 ± 반복 간 표본 표준편차이다. 검색 Recall은 정답 근거 중 검색된 비율, Precision은 검색 근거 중 정답 비율이며, linked-gold recall은 링크 경유 정답 근거의 Recall이다. CP/CR/AC는 RAGAS Context Precision/Recall/Answer Correctness이다[10]. 생성·평가 judge는 같은 `gpt-5.6-luna` 모델이고 검색·평가 임베딩은 각각 `text-embedding-3-small`, `text-embedding-3-large`를 사용했다.

<!-- columnbreak -->

표 1. 그래프 질의 검색 결과 (n=20, `hybrid_rr`=`hybrid_rerank`)

| 변형 | Recall | Precision | 링크 정답 Recall |
|---|---:|---:|---:|
| bm25 | 0.592±0.000 | 0.260±0.000 | 0.275±0.000 |
| dense | 0.383±0.000 | 0.170±0.000 | 0.000±0.000 |
| hybrid | 0.521±0.000 | 0.230±0.000 | 0.150±0.000 |
| hybrid_rr | 0.586±0.019 | 0.781±0.038 | 0.233±0.014 |
| link_all | 0.850±0.014 | 0.721±0.002 | 0.750±0.000 |
| proposed | 0.839±0.046 | 0.742±0.022 | 0.708±0.063 |

표 2. 그래프 질의 문맥·답변 결과 (n=20)

| 변형 | CP | CR | AC |
|---|---:|---:|---:|
| bm25 | 0.794±0.028 | 0.778±0.012 | 0.734±0.006 |
| dense | 0.511±0.050 | 0.625±0.003 | 0.662±0.021 |
| hybrid | 0.759±0.052 | 0.714±0.000 | 0.683±0.028 |
| hybrid_rr | 0.946±0.053 | 0.785±0.016 | 0.745±0.016 |
| link_all | 0.877±0.008 | 0.938±0.007 | 0.758±0.029 |
| proposed | 0.923±0.033 | 0.916±0.011 | 0.756±0.012 |

<!-- columnbreak -->

표 3. 그래프 사례별 paired 차이 (LA=`link_all`, HR=`hybrid_rerank`, P=`proposed`; R=Recall, LGR=링크 정답 Recall)

| 비교 / 지표 | Δ [95% CI] | p | 쌍 / 비영 |
|---|---:|---:|---:|
| LA−HR / R | +0.264 [0.158, 0.367] | <.001 | 20/14 |
| LA−HR / LGR | +0.517 [0.308, 0.717] | <.001 | 20/12 |
| LA−HR / CP | −0.069 [−0.136, −0.004] | .077 | 20/13 |
| LA−HR / AC | +0.013 [−0.030, 0.070] | .784 | 20/20 |
| P−HR / R | +0.253 [0.161, 0.344] | <.001 | 20/13 |
| P−HR / LGR | +0.475 [0.283, 0.667] | <.001 | 20/12 |
| P−HR / CP | −0.023 [−0.075, 0.031] | .774 | 20/13 |
| P−HR / AC | +0.011 [−0.034, 0.071] | .596 | 20/20 |
| P−LA / R | −0.011 [−0.058, 0.025] | .750 | 20/4 |
| P−LA / LGR | −0.042 [−0.117, 0.017] | .500 | 20/3 |
| P−LA / CP | +0.046 [0.009, 0.089] | .067 | 20/14 |
| P−LA / AC | −0.002 [−0.022, 0.021] | .622 | 20/20 |

각 사례 점수를 3회 평균한 뒤 짝지었다. CI는 사례를 10,000회 재표집한 percentile bootstrap이고, p는 0 차이를 제외한 양측 exact Wilcoxon이다. p값은 다중 비교 보정 전 탐색값이며 일부 사례가 규정·링크를 공유한다. 개발 그래프 5건에서 hybrid_rerank/link_all/proposed의 Recall은 0.478/0.667/0.689, 링크 정답 Recall은 0.067/0.400/0.433이었다. 별도 신규 15건에서는 각각 0.622/0.911/0.889, 0.289/0.867/0.800이었다. 신규 그래프 15건은 승인 링크 36개 중 서로 다른 링크 15개를 골라 양쪽 원문을 바탕으로 LLM이 작성했고 검색 결과로 조정하지 않았다. 그러나 링크 자체에서 사례를 만들었으므로 링크 방식에 유리할 수 있으며, 신규 라벨은 아직 저자 검수 전이다.

## 4. 논의 및 결론

전체 그래프 사례에서 링크 기반 방식은 `hybrid_rerank`보다 Recall과 링크 정답 Recall을 크게 높였다. 선택 재정렬은 `link_all` 대비 평균 Recall을 0.011 낮추면서 CP를 0.046 높였다. CP의 bootstrap 구간은 양수였지만 exact Wilcoxon p=.067이므로 확정적 차이로 해석하지 않는다. 첫 재정렬도 `hybrid` 대비 Precision을 0.230에서 0.781, CP를 0.759에서 0.946으로 높였다.

이 검색 개선은 답변 정확도로 거의 이어지지 않았다: `hybrid_rerank`와 `proposed`의 AC는 0.745와 0.756으로 비슷하다. 생성 모델이 불완전한 근거의 빈틈을 보완했거나 RAGAS AC가 근거 품질 변화를 충분히 구분하지 못했을 수 있다. 같은 모델이 생성과 채점을 수행했으므로, 향후 규정 실무자의 블라인드 답변·근거 검수가 필요하다.

이 코퍼스의 그래프 Recall은 BM25(0.592), hybrid(0.521), dense(0.383) 순이었다. Dense 기준선은 조항 단위가 부모 청크의 임베딩을 물려받아 이웃 조항이 같은 점수로 묶이는 표현 한계가 있다. 따라서 관찰된 dense 열세는 이 기준선의 특성이며 일반적인 dense 검색의 한계로 확대하지 않는다.

결과는 승인 링크 기반 확장이 이 사례들에서 교차문서 근거 회수를 돕는다는 탐색적 근거다. 15/20 그래프 사례가 링크에서 초안된 점, 미검수 정답, 사례 간 규정·링크 공유, 실행 당시 승인 링크 스냅샷 부재가 일반화를 제한한다. 연결 근거가 누락되어도 현 시스템은 직접 근거로 답할 수 있고 이를 알리는 경고가 없다. 사람 검수, 링크 변경 이력 추적, 불완전 답변 경고를 검증하기 전에는 실제 운전 판단에 사용해서는 안 된다.

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
