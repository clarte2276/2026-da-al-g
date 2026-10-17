# 교차 문서 그래프 링크 판정에서 Jev와 대규모 언어 모델의 비교

*Comparing Jev and Large Language Models for Cross-Document Graph Link Decisions*

## 요약

동일한 하이브리드 후보를 사용해 Jev pair/choice, GPT-5.6 Luna pair/list 및 Jev–LLM cascade의 링크 선택을 비교했다. 주 평가 단위인 슬라이드–조항 엣지에서 K=10 후보 생성기는 승인 대상 엣지 209개 중 42개(0.201), K=50은 103개(0.493)를 포함했다. pair-level 비교에서 Jev pair는 LLM pair보다 종단 간 F1이 낮았고(차이 −0.049, 95% 군집 bootstrap CI [−0.092, −0.008]), precision 차이 구간은 0을 포함했다. 이는 단일 철도 도메인과 불완전한 승인 그래프에서 얻은 파일럿 결과다.

## 1. 서론 및 관련 연구

검색 증강 생성은 외부 근거를 언어 모델 답변에 연결하고[1], GraphRAG 및 KG²RAG는 관계 그래프를 사용해 관련 문맥을 확장한다[2,3]. 문서 관계 추출과 법률 상호참조 연구는 서로 다른 문서 단위 사이의 연결을 다뤄 왔다[4–6]. 확률 보정은 분류 품질과 구분해 평가할 필요가 있으며[7], Jev의 구조화 판단과 불확실한 쌍만 전달하는 cascade는 운영 비용을 바꿀 수 있다[8–10]. 본 연구는 새 검색 알고리즘의 우월성을 주장하지 않고, 철도 안내 슬라이드와 규정 조항 사이의 승인 링크를 만드는 판정기·출력 형식 조합을 비교한다.

## 2. 방법

후보 순위는 저장된 cosine 유사도(가중치 0.6)와 BM25(0.4)를 결합했으며, 모든 판정기에 같은 후보를 제공했다. 규정은 354개 조항 단위다. 정답은 승인된 링크 기록 36건의 대상 조항을 각 승인 페이지와 교차해 만든 209개 슬라이드–조항 엣지다. 음성은 77개 미연결 페이지에서 뽑은 80개 추출이며, 세 중복 추출은 가중치에 남겼다. 주 지표도 이 슬라이드–조항 단위로 계산했다. 이는 승인된 각 페이지에서 어떤 조항 링크를 선택했는지와 미연결 페이지의 오선택을 같은 단위에서 세기 위함이다.

Jev pair와 LLM pair는 후보마다 yes/no 확률을 내고 cascade는 Jev 확률 0.20–0.80의 쌍만 같은 LLM pair 판단에 전달한다. Jev choice는 후보 중 하나 또는 none을 고르는 단일 선택이고, LLM list는 여러 조항을 고르는 출력이다. 따라서 pair·cascade의 p≥0.5 이진 엣지 판정과 달리 choice/list는 native 선택 결과를 직접 평가했다. 선택 출력은 precision·recall·FP 엣지 수와 top-1 일치율을 보고하고 pair-level ECE에서 제외했다.

## 3. 결과

후보 생성기는 K=10에서 대상 209개 중 42개, K=50에서 103개를 포함했다. 표 1의 종단 간 값은 후보 누락을 false negative로 포함하고, 후보 내 값은 누락된 대상만 분모에서 제외한다. 각 셀의 세 값은 P/R/F1 순서이며, 수치는 세 API 반복의 평균±표본 표준편차다.

표 1. 슬라이드–조항 단위 링크 판정 결과

| K·판정기 | 종단 간 P/R/F1 | 후보 내 P/R/F1 | Pair ECE |
|---|---:|---:|---:|
| 10 Jev pair | 0.203±0.007<br>0.078±0.003<br>0.113±0.004 | 0.203±0.007<br>0.389±0.014<br>0.266±0.009 | 0.121±0.001 |
| 10 Jev choice | 0.343±0.004<br>0.073±0.003<br>0.121±0.004 | 0.343±0.004<br>0.365±0.014<br>0.354±0.009 | — |
| 10 LLM pair | 0.175±0.009<br>0.152±0.007<br>0.162±0.008 | 0.175±0.009<br>0.754±0.036<br>0.284±0.014 | 0.172±0.003 |
| 10 LLM list | 0.137±0.009<br>0.081±0.005<br>0.102±0.006 | 0.137±0.009<br>0.405±0.024<br>0.205±0.013 | — |
| 10 Cascade | 0.235±0.054<br>0.159±0.007<br>0.188±0.013 | 0.235±0.054<br>0.794±0.036<br>0.360±0.061 | 0.140±0.024 |
| 50 Jev pair | 0.199±0.001<br>0.179±0.003<br>0.188±0.001 | 0.199±0.001<br>0.362±0.006<br>0.257±0.001 | 0.064±0.000 |
| 50 Jev choice | 0.440±0.009<br>0.105±0.000<br>0.170±0.001 | 0.440±0.009<br>0.214±0.000<br>0.288±0.002 | — |
| 50 Cascade | 0.153±0.040<br>0.244±0.068<br>0.188±0.050 | 0.153±0.040<br>0.495±0.138<br>0.233±0.062 | 0.068±0.003 |

Jev pair−LLM pair의 ΔF1은 −0.049 [−0.092, −0.008], Δ재현율은 −0.073 [−0.115, −0.034]였고 Δ정밀도는 +0.028 [−0.050, +0.124]로 0을 포함했다. pair-level ECE 차이 −0.051 [−0.067, −0.035]는 승인 그래프 기준의 오차 차이다. Cascade−LLM pair의 ΔF1은 +0.026 [−0.013, +0.067]로 0을 포함해 우월성을 뒷받침하지 않는다. 구간은 승인 기록 36개와 고유 음성 페이지 77개를 층화해 2,000회 재표집한 95% 군집 bootstrap이며, 도메인 일반화 구간은 아니다.

Native 선택 출력의 K=10 Jev choice는 종단 간/후보 내 P/R/F1이 각각 0.343/0.073/0.121 및 0.343/0.365/0.354였고, 오선택 엣지는 29.3±0.6개, 양성 페이지 top-1 일치율은 0.192±0.007이었다. LLM list는 0.137/0.081/0.102 및 0.137/0.405/0.205, 오선택 107.0±6.1개, top-1 0.150±0.022였다. K=50 Jev choice의 종단 간/후보 내 F1은 0.170/0.288, top-1은 0.275±0.000, FP=28.0±1.0개였다. Top-1은 80개 양성 페이지에서 선택한 조항이 승인 대상 중 하나인지 센 값이다. choice는 단일 선택, list는 선택 항목 중 confidence가 가장 높은 조항으로 계산했다. 선택지 분포와 후보별 확률의 공동 사건은 달라 cross-format ECE를 계산하지 않았다.

표 2의 K=10 비용·시간은 세 반복 합계와 회당 평균(합계/3)이다. 시간은 순차 API 호출 지연 합계이며 로컬 처리와 후속 검색을 제외한다.

표 2. K=10 판정 비용 및 API 호출 시간

| 판정기 | 3회 비용 합계 (USD) | 3회 시간 합계 (초) | 회당 평균 (USD / 초) |
|---|---:|---:|---:|
| Jev pair | 0.236291 | 148.94 | 0.078764 / 49.65 |
| Jev choice | 0.121470 | 129.75 | 0.040490 / 43.25 |
| LLM pair | 0.726212 | 668.05 | 0.242071 / 222.68 |
| LLM list | 0.254104 | 284.13 | 0.084701 / 94.71 |
| Cascade 전체 (Jev+LLM) | 0.392360 | 221.49 | 0.130787 / 73.83 |

비용 산정은 기록된 토큰 사용량과 실험일의 OpenAI 입력/캐시 입력/출력 단가 및 Jev 입력 단가를 사용했다[9,11]. K=50 cascade의 파이프라인 증분 비용은 세 반복 합계 USD 1.209444/770.93초이며(회당 USD 0.403148/256.98초), K=10 Jev 재사용 포함 누적은 USD 1.601804/992.41초(회당 USD 0.533935/330.80초)다. 후속 검색은 K=10 링크 집합으로 37개 질의를 한 번 평가한 탐색 결과다. 전체 질의 Recall/MRR/nDCG@10은 Jev pair 0.818/0.986/0.851, LLM pair 0.813/0.968/0.840, cascade 0.840/0.986/0.869였으며 반복 구간은 없다.

## 4. 결론 및 한계

본 분석은 동일 후보 생성기에서 판정 형식별 승인 엣지 일치와 비용을 비교했다. 링크 기록 단위 후보 포괄은 K=10 26/96, K=50 49/96이었으며, 논문의 주 품질 단위는 페이지별 슬라이드–조항 엣지로 유지했다. precision·FP·ECE는 승인 그래프와의 일치 지표이며 미승인 후보가 실제 무관하다고 확인된 결과는 아니다.

한계는 명시적으로 네 가지다. 첫째, K=10 downstream/RAGAS 추가 반복, K=50 downstream, K=100 추가 Jev/cascade 반복은 API 크레딧 부족으로 미완료이며 K=100 LLM pair는 800개 중 302개 호출 뒤 중단되어 성능 추정이 없다. 둘째, 고확률 미승인 후보 40건의 사람 FP 검수가 대기 중이다. 셋째, 자료는 단일 철도 도메인에 한정된다. 넷째, 정답은 승인 링크 36건뿐이다. 따라서 운영 우위나 실제 관련성 정밀도, 타 도메인 일반화를 주장하지 않는다.

## 참고문헌

[1] P. Lewis et al., “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” NeurIPS, vol. 33, pp. 9459–9474, 2020.

[2] D. Edge et al., “From Local to Global: A Graph RAG Approach to Query-Focused Summarization,” arXiv:2404.16130, 2024.

[3] X. Zhu et al., “Knowledge Graph-Guided Retrieval Augmented Generation,” NAACL-HLT, pp. 8912–8924, 2025.

[4] C. Min et al., “Efficient Knowledge Graph Construction and Retrieval from Unstructured Text for Large-Scale RAG Systems,” arXiv:2507.03226, 2025.

[5] G. Li et al., “Revisiting Large Language Models as Zero-shot Relation Extractors,” Findings EMNLP, pp. 6877–6892, 2023.

[6] N. Sannier et al., “An Automated Framework for Detection and Resolution of Cross References in Legal Texts,” Requirements Engineering, vol. 22, no. 2, pp. 215–237, 2017.

[7] C. Guo et al., “On Calibration of Modern Neural Networks,” ICML, PMLR 70, pp. 1321–1330, 2017.

[8] D. Almeida, “Introducing System One Models & Jev,” TypeSafe AI, https://typesafe.ai/blog/introducing-system-one-models-and-jev, accessed 2026-10-17.

[9] TypeSafe AI, “System One API documentation,” https://docs.typesafe.ai/llms.txt, accessed 2026-10-17.

[10] L. Chen, M. Zaharia, and J. Zou, “FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance,” arXiv:2305.05176, 2023.

[11] OpenAI, “GPT-5.6 Luna model pricing,” https://developers.openai.com/api/docs/models/gpt-5.6-luna, accessed 2026-10-17.