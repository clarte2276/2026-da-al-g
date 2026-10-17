# 교차 문서 그래프 링크 판정을 위한 Jev와 대규모 언어 모델 비교

*Comparing Jev and Large Language Models for Cross-Document Graph Link Decisions*

## 요약

그래프 검색 증강 생성에서 링크 판정의 품질·비용 절충을 살피기 위해, 동일한 하이브리드 후보에 Jev pair/choice, GPT-5.6 Luna pair/list, Jev-LLM cascade를 적용했다. 사람 승인 링크 36건의 목표 96개 중 후보 생성기가 K=10에서 26개(0.271), K=50에서 49개(0.510)를 포괄했다. K=10 링크 기록 단위에서 Jev choice는 LLM pair보다 평균 비용과 순차 호출 시간이 낮고(USD 0.121470, 129.75초 대 USD 0.726212, 668.05초), 반복 판정 일치율과 승인 gold 기준 ECE도 낮았다(0.996 대 0.945; 0.064 대 0.122). 반면 재현율과 F1은 낮았다(0.062 대 0.222; 0.100 대 0.176). Jev choice−LLM pair의 paired 군집 bootstrap 95% CI는 재현율 차이 [−0.246, −0.092], F1 차이 [−0.130, −0.026]이며 정밀도 차이 구간은 0을 포함한다. Cascade는 K=10에서 평균 F1이 LLM pair보다 높았지만 그 차이의 신뢰구간은 0을 포함했고, K=50에서 Jev choice를 가장 나은 단일 절충으로 대체하지 못했다. 불완전한 gold, 작은 단일 도메인 표본과 미실행 평가를 고려해 결과를 파일럿 비교로 한정한다.

## 1. 서론 및 관련 연구

검색 증강 생성(RAG)은 검색 근거를 언어 모델 답변에 연결하며[1], GraphRAG와 KG²RAG는 문서 관계를 그래프로 구성하거나 검색 seed에서 관련 문맥을 확장한다[2,3]. 그래프 구성에는 비LLM 추출이나 관계 분류도 사용되며, 문서 간 관계와 법률 상호참조는 단순 문자열 일치만으로 해결되지 않을 수 있다[4–6]. 그러나 검색 성능과 별개로 실제 링크 후보를 어떤 판정기로 선택할지, 그 확률을 신뢰할 수 있는지, 비용이 얼마인지는 운영상 남는 질문이다.

확률의 보정은 정확도와 별도로 평가할 필요가 있다[7]. Jev는 구조화 선택과 확률 응답을 제공하는 System One 모델이며[8,9], 불확실한 판단만 상위 모델로 전달하는 cascade는 비용과 품질을 절충하는 방법이다[10]. 본 연구는 새 그래프 검색 알고리즘을 제안하지 않고, 한 철도 운영 도메인의 현장 안내자료와 규정 조항 사이에 이미 승인된 `REFERENCES` 링크를 대상으로 같은 후보 생성 조건에서 판정 형식별 품질, 보정, 비용 및 후속 검색을 비교한다.

## 2. 방법

후보 생성은 저장된 임베딩 cosine 유사도(가중치 0.6)와 BM25(0.4)를 결합한 순위로 모든 판정기에 공유했다. 규정 말뭉치는 354개 조항 단위다. 주 비교는 슬라이드마다 상위 K=10 후보를 사용하고, 후보 포괄과 확장 결과를 K=50에서도 집계했다. 평가 자료는 사람 승인 링크 기록 36건과 목표 조항 범위 96개, 긍정 안내 슬라이드 80쪽이다. 대조군은 미연결 슬라이드 77쪽을 한 번씩 포함하고 3회를 다시 추출해 총 80회로 구성했다.

Jev pair와 LLM pair는 후보 쌍마다 이진 판정하고, Jev choice는 슬라이드마다 후보 한 조항 또는 `none`을 고르며 LLM list는 0개 이상의 후보를 반환한다. LLM은 `gpt-5.6-luna`를 사용했다. Cascade는 Jev pair 확률이 0.20–0.80인 쌍만 같은 LLM pair 판정에 넘기고 나머지는 Jev 결과를 유지했다. 모든 주 결과의 수락 기준은 p≥0.5로 실험 설정에 고정되어 있었으며, 별도 holdout에서 임계값을 선택하지 않았다.

## 3. 실험

### 3.1 후보 포괄률과 엣지 품질

표 1의 주 지표는 링크 기록 단위다. 각 승인 기록의 목표 조항 점수는 그 기록에 속한 슬라이드 점수 중 최댓값으로 집계했다. 후보에서 누락된 gold는 종단 간 재현율과 ECE 계산에 확률 0으로 포함한다. K=10은 96개 목표 중 26개(0.271), K=50은 49개(0.510)만 후보에 포함했다. K=50에서 Jev choice의 조건부 P/R/F1은 0.674/0.224/0.337, ECE는 0.004였지만, 누락 gold를 포함하면 R/F1/ECE는 0.115/0.196/0.011이다. 같은 K의 cascade는 종단 간 P/R/F1 0.106/0.295/0.156, ECE 0.080이었다. 조건부와 종단 간 수치는 분모가 다르며, 후보 누락을 판정기 오류와 혼합하지 않는다.

표 1. 후보 포괄률과 링크 기록 단위의 종단 간 판정 결과

| K·판정기 | 후보 포함 목표 | P / R / F1 @ 0.5 | ECE / 반복 일치율 |
|---|---:|---:|---:|
| 10 Jev pair | 26/96 (0.271) | .123±.009<br>.087±.006<br>.102±.007 | .079±.001<br>.991 |
| 10 Jev choice | 26/96 (0.271) | .247±.015<br>.062±.000<br>.100±.001 | .064±.001<br>.996 |
| 10 LLM pair | 26/96 (0.271) | .146±.010<br>.222±.006<br>.176±.009 | .122±.005<br>.945 |
| 10 LLM list | 26/96 (0.271) | .126±.012<br>.160±.006<br>.140±.010 | .101±.006<br>.963 |
| 10 Cascade | 26/96 (0.271) | .177±.047<br>.205±.012<br>.187±.023 | .096±.026<br>.936 |
| 50 Jev choice | 49/96 (0.510) | .674±.023<br>.115±.000<br>.196±.001 | .011±.000<br>— |
| 50 Cascade | 49/96 (0.510) | .106±.025<br>.295±.071<br>.156±.037 | .080±.002<br>— |

확률 지표는 세 API 반복의 평균±표본 표준편차다. 양성은 기록 안 여러 슬라이드 중 최대 점수, 음성은 80회 표집을 별도 그룹으로 집계했다. ECE는 승인 gold와 10개 동일 폭 구간을 사용하며 K=10 링크 기록 단위 end-to-end 분모는 1,477(후보 포함 1,407), K=50은 6,711(후보 포함 6,664)이다. 반복 일치율은 후보 엣지의 p≥0.5 판정이 세 번 모두 같았던 비율이며 정확도가 아니다. 링크 기록 36개와 고유 음성 슬라이드 77개를 군집으로 한 paired bootstrap 2,000회(seed 20261018)에서 Jev choice−LLM pair의 ΔF1은 −0.076 (95% CI [−0.130, −0.026]), Δ재현율은 −0.160 [−0.246, −0.092], Δ정밀도는 +0.102 [−0.022, +0.243], ΔECE는 −0.058 [−0.077, −0.037]였다. 따라서 재현율·F1·ECE 차이는 구간이 0을 포함하지 않지만 정밀도 차이는 불확실하다. Cascade−LLM pair의 ΔF1은 +0.011 [−0.033, +0.054]로 0을 포함한다. 반복 SD는 API 호출 변동이고, 군집 구간도 단일 자료의 표집 변동을 나타낼 뿐 도메인 일반화 근거는 아니다.

판정기와 출력 형식 효과도 완전히 분리되지는 않는다. 별도 슬라이드–조항 엣지 단위 형식 패리티에서 pair 출력을 top-1로 바꾸자 Jev의 P/F1은 0.203/0.113에서 0.315/0.119로, LLM은 0.175/0.162에서 0.227/0.118로 달라졌다. 따라서 표 1은 모델 효과만이 아니라 pair·choice·list의 운영 형식을 포함한 비교이며, 공통 다중 라벨 yes/no 재실행 결과로 해석하지 않는다.

### 3.2 비용과 지연

표 2는 K=10의 세 반복 비용 합계와 순차 API 호출 시간이다. 캐시 입력은 전체 입력 토큰의 하위 집합으로 별도 표기했다. 비용은 GPT-5.6 Luna 입력 USD 0.20/M, 캐시 입력 USD 0.02/M, 출력 USD 1.20/M, Jev 입력 USD 0.042/M(출력 무료) 기준이며 2026-10-17 확인 가격을 사용했다[9,11]. 지연은 API 호출 시간 합계이며 로컬 파싱·후보 생성·후속 검색은 포함하지 않는다.

표 2. K=10 판정 호출 비용과 순차 API 시간 (3회 합계)

| 판정기 | 호출 수 / 입력 토큰 | 캐시 입력 / 출력 토큰 | USD / 초 |
|---|---:|---:|---:|
| Jev pair | 480<br>5,625,972 | 0 / 93,120 | 0.236291<br>148.94초 |
| Jev choice | 480<br>2,892,135 | 0 / 108,781 | 0.121470<br>129.75초 |
| LLM pair | 74<br>5,808,287 | 3,191,376 / 115,835 | 0.726212<br>668.05초 |
| LLM list | 61<br>2,430,530 | 1,576,834 / 43,190 | 0.254104<br>284.13초 |
| Cascade 전체 | 492<br>6,334,966 | 0 / 105,012 | 0.392360<br>221.49초 |

Cascade의 전체 값은 Jev pair USD 0.236291·148.94초와 불확실 쌍 LLM 단계 USD 0.156069·72.55초의 합이다. K=50 Jev choice는 USD 0.395796·168.62초, cascade는 증분 USD 1.209444·770.93초이며 K=10 Jev 재사용 포함 시 USD 1.601804·992.41초다. 재현 설정은 Jev `jev-latest`(응답 `jev-1.13.0`), `gpt-5.6-luna`, 2026-10-17 02:01–05:10 UTC 캐시 호출이다. Jev pair/choice는 `noul`/`choice`; OpenAI는 JSON, temperature 0, reasoning none, 최대 4,096 토큰을 썼다. 표본 seed는 20261017, 후보 가중치는 0.6/0.4이며 프롬프트 파일과 SHA-256은 재분석 부록에 있다. 코드 commit과 원본 DB snapshot hash는 기록되지 않았다. ECE는 승인 기록 기준의 보정 일치도다.

### 3.3 후속 검색

K=10 링크 집합은 세 반복의 p≥0.5 다수결로 만들었다. GPT-5.6 Luna와 `text-embedding-3-small`로 37개 질의를 한 번(r1) 평가한 Recall/MRR/nDCG@10은 Jev pair 0.818/0.986/0.851, LLM pair 0.813/0.968/0.840, cascade 0.840/0.986/0.869, 승인 gold 0.912/0.982/0.919였다. `via_link`가 정의된 20개 질의의 linked-gold recall은 순서대로 0.350/0.400/0.450/0.750이다. 단일 실행이며 질의별 변동 구간이나 사람의 답변 검수는 없다.

## 4. 결론 및 한계

Jev choice는 K=10 LLM pair보다 비용·순차 호출 시간·반복 일치율·승인 gold ECE가 낮은 대신 재현율과 F1도 낮았다. 정밀도 차이 구간은 0을 포함했다. Cascade의 K=10 평균 F1은 높았지만 paired 구간은 0을 포함하며, K=50에서는 Jev choice의 precision/F1과 cascade의 recall이 더 높았다. 따라서 cascade가 전 조건에서 최선이라는 근거는 없다.

Gold는 승인 링크 36건뿐이라 미승인 후보의 관련성은 미검증이다. Precision·ECE는 승인 그래프와의 일치이며, 고확률 예측 40건의 사람 검수도 미완료다. 자료는 단일 도메인이고 후보 포괄률은 K=10/50에서 0.271/0.510이다. API 크레딧 부족으로 K=50 downstream과 추가 반복은 실행하지 않았다. K=100 Jev·cascade는 1회만 완료했고 LLM pair는 800개 요청 중 302개 뒤 중단되어 성능값이 없다. 결과는 같은 후보 생성기의 파일럿 절충 비교다.

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
