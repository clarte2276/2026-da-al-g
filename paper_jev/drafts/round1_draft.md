# 교차 문서 그래프 링크 구성을 위한 Jev와 대규모 언어 모델의 비교

*Comparing Jev and Large Language Models for Cross-Document Graph Link Construction*

## 요약

그래프 검색 증강 생성(Graph RAG)의 문서 간 링크 판정에서 TypeSafe Jev와 gpt-5.6-luna 기반 LLM, 두 모델을 잇는 cascade를 같은 후보로 비교했다. 승인 링크 36건의 96개 목표 엣지를 평가한 결과, K=10에서 Jev choice는 LLM pair보다 정밀도(0.247 대 0.146)와 결정 일치율(0.996 대 0.945)이 높고 비용(USD 0.121470 대 0.726212)과 누적 지연(129.75초 대 668.05초)이 낮았으나 재현율은 낮았다(0.062 대 0.222). K=50 Jev choice는 후보가 덮은 49/96 엣지에서 정밀도 0.674, ECE 0.004였지만 전체 재현율은 0.115에 그쳤다. K=10 cascade는 LLM pair보다 F1이 높고 비용·지연이 낮았으나, K=50에서는 Jev choice의 F1이 더 높았다. 후보 누락, 불완전한 gold, 소규모·단일 도메인 자료를 고려하면 어느 판정기가 우월하다고 결론 내릴 수 없다.

## 1. 서론 및 관련 연구

검색 증강 생성(RAG)은 검색 근거를 언어 모델 응답에 연결하고[1], GraphRAG와 KG²RAG는 문서 관계를 그래프로 구성하거나 검색 seed에서 관련 근거를 확장한다[2,3]. 의존 구문 기반 그래프 구성은 LLM 호출을 줄이는 대안이며[4], 법률 문서 상호참조 해소는 문서 구조와 참조 표현을 사용한다[5]. 본 연구는 새 그래프 검색 알고리즘을 제안하지 않는다. 철도 현장 안내 슬라이드와 규정 조항 사이의 링크 후보를 만드는 동일 조건에서 Jev와 범용 LLM의 판정 품질·확률 보정·호출 비용을 비교한다.

Jev의 구조화 판단 API는 선택지별 확률을 반환하고[6,7], 확률을 신뢰도처럼 사용하는 경우 보정도 품질과 별도로 평가해야 한다[8]. 불확실한 요청만 상위 모델로 전달하는 cascade는 비용과 품질의 절충 방법이다[9]. 여기서는 동일 후보에 대한 pair, choice, list 판단과 cascade를 측정해, 정밀도와 재현율·비용 사이의 절충이 실제 링크 구성에서 성립하는지 살핀다.

## 2. 방법

모든 판정기는 저장된 임베딩 유사도(가중치 0.6)와 BM25(0.4)를 결합한 순위에서 얻은 동일 후보를 사용한다. 규정 말뭉치는 재구성한 354개 조항 단위다. K=10을 주 비교로 하고 후속 비교는 K=50까지 확장했다. Jev pair는 슬라이드–조항 쌍마다 이진 판정하고, Jev choice는 슬라이드마다 후보 중 조항 하나 또는 없음(거절)을 선택한다. LLM pair는 gpt-5.6-luna에 쌍별 판정을 요청하고, LLM list는 한 요청에서 선택 조항 ID와 긍정 확률을 반환한다. Cascade는 Jev 확률이 0.20 이상 0.80 이하인 쌍만 같은 LLM pair 판정으로 넘긴다.

## 3. 실험

### 3.1 설정 및 후보 포괄률

평가 gold는 안내 자료에서 규정으로 연결된 사람 승인 `REFERENCES` 링크 36건, 목표 조항 범위 96개이며, 긍정 안내 슬라이드 80쪽에 해당한다. 비교를 위해 미연결 슬라이드 77쪽에서 복원추출한 80건을 더해 총 160쪽을 평가했다. 각 링크–조항 목표의 점수는 승인된 원본 선택에 포함된 슬라이드들의 최대 확률이다. 후보는 임베딩 API 호출 없이 기존 벡터와 BM25로 계산했다. 표 1에서 K=100도 gold 엣지 96개 중 69개만 포괄한다.

표 1. 후보 수에 따른 승인 gold 포괄률

| K | 후보/슬라이드 | 엣지 재현율 | 전체 조항 포괄 링크 |
|---:|---:|---:|---:|
| 10 | 10.0 | 26/96 (0.271) | 6/36 (0.167) |
| 20 | 20.0 | 35/96 (0.365) | 9/36 (0.250) |
| 50 | 50.0 | 49/96 (0.510) | 11/36 (0.306) |
| 100 | 100.0 | 69/96 (0.719) | 19/36 (0.528) |

### 3.2 엣지 품질, 보정 및 비용

주 비교의 모든 판정기는 슬라이드마다 동일한 상위 10개 후보를 받았다. precision(P), recall(R), F1은 확률 임계값 0.5에서 계산했으며, 점수 기준선만 원래 하이브리드 점수를 사용한다. 표 2의 확률 지표는 세 반복의 평균±표본 표준편차다. 기대 보정 오차(ECE)는 10개 균등 구간을 쓰고 누락 gold에는 확률 0을 부여했다. 결정 일치율은 세 반복에서 동일한 임계값 판정이 나온 후보 엣지 비율이다. 비용은 3회 실행 합계이며, 총 지연은 순차 API 호출 시간의 합으로 로컬 처리 시간은 제외한다.

표 2. K=10 엣지 판정 및 호출 결과

| 판정기 | P / R / F1 | ECE / 일치율 | USD / 초 |
|---|---|---|---|
| 하이브리드 점수 | 0.000 / 0.000 / 0.000 | 해당 없음 / 1.000 | 0.000000 / 0.00 |
| Jev pair | 0.123±0.009 / 0.087±0.006 / 0.102±0.007 | 0.079±0.001 / 0.991 | 0.236291 / 148.94 |
| Jev choice | 0.247±0.015 / 0.062±0.000 / 0.100±0.001 | 0.064±0.001 / 0.996 | 0.121470 / 129.75 |
| LLM pair | 0.146±0.010 / 0.222±0.006 / 0.176±0.009 | 0.122±0.005 / 0.945 | 0.726212 / 668.05 |
| LLM list | 0.126±0.012 / 0.160±0.006 / 0.140±0.010 | 0.101±0.006 / 0.963 | 0.254104 / 284.13 |
| Cascade | 0.177±0.047 / 0.205±0.012 / 0.187±0.023 | 0.096±0.026 / 0.936 | 0.392360 / 221.49 |

K=10에서는 LLM pair가 Jev choice보다 재현율이 높지만(0.222 대 0.062), 정밀도는 낮고 비용은 약 6배, 총 지연은 약 5배였다. Cascade는 LLM pair보다 F1이 높고 비용과 지연이 낮았으나, Jev choice보다 정밀도가 낮고 보정 오차가 컸다. K=50에서 Jev choice의 후보 포괄률은 49/96 (0.510)이었다. 포괄된 gold만 분모에 둔 조건부 지표는 P=0.674±0.023, R=0.224±0.000, F1=0.337±0.003, ECE=0.004±0.000이었다. 후보에서 빠진 gold를 false negative로 포함하면 R=0.115±0.000, F1=0.196±0.001이다. 같은 K의 Cascade는 조건부 R=0.578±0.139로 더 높지만 P=0.106±0.025, F1=0.179±0.043, ECE=0.088±0.002였고, 전체 R/F1은 0.295±0.071/0.156±0.037이었다. K=50 3회 비용은 Jev choice USD 0.395796, Jev 호출 재사용을 포함한 Cascade USD 1.601804였으며, 이 후속 비교의 지연은 집계되지 않았다. 따라서 cascade는 K=10에서 LLM pair보다 유리한 비용–F1 점을 보였지만, K=50에서 최선의 절충은 아니었다.

### 3.3 후속 검색

K=10 링크로 평가한 전체 37개 질의에서 retrieval recall/MRR/nDCG@10/링크 gold 재현율은 링크 없음 0.773/0.986/0.815/0.200, Jev pair 0.818/0.986/0.851/0.350, LLM pair 0.813/0.968/0.840/0.400, Cascade 0.840/0.986/0.869/0.450이었다. 정답 링크 집합은 0.912/0.982/0.919/0.750이었다. 링크 gold 재현율은 `via_link` 정답이 정의된 질의만 평균했다. K=50 최선 Jev choice와 Cascade의 downstream 평가는 API 크레딧 소진으로 실행되지 않았다. K=100 Jev 판정은 3회 중 1회만 완료했고, LLM pair는 할당량 부족으로 800개 중 302개 호출 뒤 중단되어 성능값을 산출하지 않았다.

## 4. 결론 및 한계

관측 범위에서 Jev choice는 낮은 비용·지연, 높은 결정 일치율과 높은 정밀도를 보이는 대신 재현율을 잃었다. LLM pair는 K=10에서 더 많은 승인 엣지를 찾았지만 false positive가 늘고 비용·지연이 컸다. Cascade는 K=10에서 LLM pair보다 비용과 F1의 절충이 나았지만, K=50 Jev choice를 앞서지 못했다. 가장 큰 병목은 판정기보다 후보 생성이며, K=50에도 승인 엣지의 0.510만 후보에 들어왔다.

gold는 승인 링크만 양성으로 둔 불완전 라벨이므로, 미승인 엣지는 오답이 아니라 미검토일 수 있고 precision은 현재 승인과의 일치도를 뜻한다. 평가는 한 도메인의 승인 링크 36건에 한정되며, 예측 엣지의 전문가 재판정이나 독립 답변 품질 검증은 수행하지 않았다. ECE와 임계값 결과 역시 작은 동일 자료에 대한 기술 통계이지 일반화 성능 보장이 아니다. K=50 최선 링크 세트의 downstream 결과와 완결된 대규모 LLM 비교는 없으므로, cascade의 보편적 우위를 주장하지 않는다. 결과는 문서 링크 구성 가능성의 파일럿 비교로 해석해야 한다.

## 참고문헌

[1] P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Küttler, M. Lewis, W. Yih, T. Rocktäschel, S. Riedel, and D. Kiela, “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” *Advances in Neural Information Processing Systems*, vol. 33, pp. 9459–9474, 2020.

[2] D. Edge, H. Trinh, N. Cheng, J. Bradley, A. Chao, A. Mody, S. Truitt, D. Metropolitansky, R. O. Ness, and J. Larson, “From Local to Global: A Graph RAG Approach to Query-Focused Summarization,” arXiv:2404.16130, 2024.

[3] X. Zhu, Y. Xie, Y. Liu, Y. Li, and W. Hu, “Knowledge Graph-Guided Retrieval Augmented Generation,” in *Proceedings of NAACL-HLT 2025*, pp. 8912–8924, 2025.

[4] C. Min, R. Mathew, J. Pan, S. Bansal, A. Keshavarzi, and A. V. Kannan, “Efficient Knowledge Graph Construction and Retrieval from Unstructured Text for Large-Scale RAG Systems,” arXiv:2507.03226, 2025.

[5] N. Sannier, M. Adedjouma, M. Sabetzadeh, and L. Briand, “An Automated Framework for Detection and Resolution of Cross References in Legal Texts,” *Requirements Engineering*, vol. 22, no. 2, pp. 215–237, 2017.

[6] D. Almeida, “Introducing System One Models & Jev,” TypeSafe AI, company blog.

[7] TypeSafe AI, “System One API documentation,” https://docs.typesafe.ai/llms.txt, accessed 2026.

[8] C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, “On Calibration of Modern Neural Networks,” in *Proceedings of the 34th International Conference on Machine Learning*, PMLR 70, pp. 1321–1330, 2017.

[9] L. Chen, M. Zaharia, and J. Zou, “FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance,” arXiv:2305.05176, 2023.
