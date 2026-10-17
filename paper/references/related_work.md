# 관련 연구 조사

조사 기준일: 2026-10-17. 본 조사는 공개 출판사·학회·학술 색인 페이지에서 제목, 저자, 연도, 수록 정보 및 초록을 확인한 문헌 30건을 정리한다. 한국 국내 연구는 7건이며, 이 중 5건은 학술지 또는 학술대회 논문집의 서지 정보를 확인했다. 한국철도학회 2026 춘계학술대회 항목 2건은 공식 프로그램의 제목·저자·발표 번호까지만 확인되며, 전문과 쪽수는 확인 필요로 표시했다.

## 후보 문헌

### A. RAG 기반 검색과 하이브리드 검색

#### 1. RAG의 기본 구조

**인용:** Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, and Douwe Kiela. 2020. “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.” *Advances in Neural Information Processing Systems*, vol. 33, pp. 9459–9474. [NeurIPS 논문 페이지](https://proceedings.neurips.cc/paper/2020/hash/6b493230-Abstract.html).

**요약:** 이 연구는 생성 모델의 파라미터 지식과 외부 비모수 메모리인 위키피디아 벡터 인덱스를 결합한 RAG 구조를 제시한다. 검색 문서를 답변 전체에 고정하는 방식과 토큰별로 바꾸는 방식을 비교하고, 지식 집약형 QA에서 외부 근거를 이용한 생성의 효과를 보였다.

**우리 연구와의 관계:** RAG의 검색-생성 기본 틀을 제공한다. 우리 연구는 벡터 근거에 더해 담당자가 승인한 문서 간 링크를 질의 관련성에 따라 확장한다.

#### 2. Dense Passage Retrieval (DPR)

**인용:** Vladimir Karpukhin, Barlas Oguz, Sewon Min, Patrick Lewis, Ledell Wu, Sergey Edunov, Danqi Chen, and Wen-tau Yih. 2020. “Dense Passage Retrieval for Open-Domain Question Answering.” In *Proceedings of EMNLP 2020*, pp. 6769–6781. [ACL Anthology](https://aclanthology.org/2020.emnlp-main.550/), DOI: [10.18653/v1/2020.emnlp-main.550](https://doi.org/10.18653/v1/2020.emnlp-main.550).

**요약:** DPR은 질문과 문단을 별도 인코더로 임베딩하는 dual-encoder 검색기를 제안하고, 공개 도메인 QA에서 BM25 대비 높은 top-20 검색 정확도를 보고했다. 이 방식은 의미 유사도 기반 검색을 RAG 파이프라인의 주요 구성요소로 정착시켰다.

**우리 연구와의 관계:** 의미 기반 초기 검색이라는 공통 기반을 제공한다. 우리 연구는 규정 조항 번호 같은 정확한 용어 검색을 위해 BM25를 결합하고, 이후 승인 링크에서 온 근거를 별도로 선별한다.

#### 3. Sparse·dense·attention 표현 결합

**인용:** Yi Luan, Jacob Eisenstein, Kristina Toutanova, and Michael Collins. 2021. “Sparse, Dense, and Attentional Representations for Text Retrieval.” *Transactions of the Association for Computational Linguistics*, vol. 9, pp. 329–345. [ACL Anthology](https://aclanthology.org/2021.tacl-1.20/), DOI: [10.1162/tacl_a_00369](https://doi.org/10.1162/tacl_a_00369).

**요약:** 이 논문은 dual encoder의 효율과 attention 기반 검색의 표현력을 결합하고, sparse 신호를 dense 검색과 혼합하는 방법을 분석한다. 희소 검색이 갖는 정확한 용어 일치의 장점을 활용해 대규모 검색에서 경쟁력 있는 성능을 보였다.

**우리 연구와의 관계:** sparse와 dense 신호를 함께 쓰는 근거를 제공한다. 우리 구현은 임베딩 유사도와 BM25 점수를 섞어 조문 번호·장비 명칭과 표현 의미를 함께 검색한다.

#### 4. 하이브리드 검색 점수 융합

**인용:** Sebastian Bruch, Siyu Gai, and Amir Ingber. 2024. “An Analysis of Fusion Functions for Hybrid Retrieval.” *ACM Transactions on Information Systems*, vol. 42, no. 1, Article 20, pp. 1–35. [arXiv:2210.11934](https://arxiv.org/abs/2210.11934), DOI: [10.1145/3596512](https://doi.org/10.1145/3596512).

**요약:** 저자들은 lexical 점수와 semantic 점수의 선형 결합 및 Reciprocal Rank Fusion을 비교하고, 각 융합 함수의 민감도와 정규화 영향을 분석한다. 이 실험에서는 적은 학습 예로 조정한 convex combination이 여러 조건에서 RRF보다 나은 결과를 보였다.

**우리 연구와의 관계:** 점수 결합 방식의 선택을 설명하는 관련 연구다. 우리 연구의 기여는 융합식 자체보다 하이브리드 검색 뒤에 승인 링크 경유 근거를 다시 관련성 평가하는 파이프라인에 있다.

#### 5. HYRR: 하이브리드 검색으로 학습 데이터를 구성한 재정렬기

**인용:** Jing Lu, Keith Hall, Ji Ma, and Jianmo Ni. 2024. “HYRR: Hybrid Infused Reranking for Passage Retrieval.” In *Proceedings of LREC-COLING 2024*, pp. 8528–8534. [ACL Anthology](https://aclanthology.org/2024.lrec-main.748/).

**요약:** HYRR은 BM25와 dense retriever가 함께 만든 후보를 사용해 견고한 reranker 학습 자료를 고른다. 저자들은 학습 시 사용한 1단계 검색기와 다른 검색기에서도 재정렬 성능이 유지되는지 평가했다.

**우리 연구와의 관계:** 재정렬이 초기 검색 후보의 편향을 줄이는 데 도움을 준다는 점에서 관련된다. 우리 파이프라인은 직접 검색 결과와 링크 경유 결과를 별도로 재정렬해 서로 다른 출처의 근거가 섞여 무조건 포함되는 일을 줄인다.

### B. LLM 기반 재정렬

#### 6. RankGPT

**인용:** Weiwei Sun, Lingyong Yan, Xinyu Ma, Shuaiqiang Wang, Pengjie Ren, Zhumin Chen, Dawei Yin, and Zhaochun Ren. 2023. “Is ChatGPT Good at Search? Investigating Large Language Models as Re-Ranking Agents.” In *Proceedings of EMNLP 2023*, pp. 14918–14937. [ACL Anthology](https://aclanthology.org/2023.emnlp-main.923/), DOI: [10.18653/v1/2023.emnlp-main.923](https://doi.org/10.18653/v1/2023.emnlp-main.923).

**요약:** RankGPT는 LLM에 질의와 후보 문단을 제시해 관련도 순으로 정렬하도록 하는 재정렬 방식을 평가한다. 연구는 zero-shot LLM 재정렬의 검색 성능과 permutation distillation을 통한 소형 모델 전이를 다룬다.

**우리 연구와의 관계:** LLM 재정렬을 초기 검색 문단뿐 아니라 링크 확장 결과에도 적용한다. 우리 연구의 재정렬 대상은 사람이 승인한 문서 연결을 따라온 근거로 제한되며, 링크 존재만으로 그 근거를 답변에 넣지 않는다.

#### 7. Pairwise Ranking Prompting

**인용:** Zhen Qin, Rolf Jagerman, Kai Hui, Honglei Zhuang, Junru Wu, Le Yan, Jiaming Shen, Tianqi Liu, Jialu Liu, Donald Metzler, Xuanhui Wang, and Michael Bendersky. 2024. “Large Language Models are Effective Text Rankers with Pairwise Ranking Prompting.” In *Findings of NAACL 2024*, pp. 1504–1518. [ACL Anthology](https://aclanthology.org/2024.findings-naacl.97/), DOI: [10.18653/v1/2024.findings-naacl.97](https://doi.org/10.18653/v1/2024.findings-naacl.97).

**요약:** Pairwise Ranking Prompting은 LLM이 한 번에 긴 목록을 정렬하기 어려울 수 있다는 점을 고려해 두 문서씩 비교하는 프롬프트를 제안한다. 저자들은 여러 검색 벤치마크에서 이 방식의 성능과 계산량을 비교한다.

**우리 연구와의 관계:** 후보 근거의 관련도 판단에 LLM을 쓰는 연구로서 재정렬 단계의 근거가 된다. 우리 연구는 일반 순위 산출뿐 아니라 직접 근거와 연결 근거의 역할을 구분해 확장 근거의 과잉 포함을 막는다.

### C. 자동 그래프·계층 구조 기반 RAG

#### 8. Microsoft GraphRAG

**인용:** Darren Edge, Ha Trinh, Newman Cheng, Joshua Bradley, Alex Chao, Apurva Mody, Steven Truitt, Dasha Metropolitansky, Robert Osazuwa Ness, and Jonathan Larson. 2024. “From Local to Global: A Graph RAG Approach to Query-Focused Summarization.” arXiv preprint, arXiv:2404.16130. [arXiv](https://arxiv.org/abs/2404.16130).

**요약:** GraphRAG는 문서에서 엔티티와 관계를 추출해 지식 그래프를 만들고, 커뮤니티 요약을 작성해 로컬·전역 질문을 다룬다. 문서 집합 전체의 주제나 관계를 묻는 쿼리를 위해 그래프 커뮤니티 수준의 요약을 검색하는 것이 핵심이다.

**우리 연구와의 관계:** 자동 엔티티·관계 추출과 커뮤니티 요약을 통해 그래프를 구성한다. 우리 연구는 그래프를 자동 생성하는 대신 관리자가 승인한 문서 구간 간 링크를 사용하고, 질문마다 링크 대상의 적합성을 다시 평가한다.

#### 9. LightRAG

**인용:** Zirui Guo, Lianghao Xia, Yanhua Yu, Tu Ao, and Chao Huang. 2025. “LightRAG: Simple and Fast Retrieval-Augmented Generation.” In *Findings of EMNLP 2025*, pp. 10746–10761. [ACL Anthology](https://aclanthology.org/2025.findings-emnlp.568/), DOI: [10.18653/v1/2025.findings-emnlp.568](https://doi.org/10.18653/v1/2025.findings-emnlp.568).

**요약:** LightRAG는 그래프와 벡터 표현을 함께 사용하며, 낮은 수준의 엔티티 검색과 높은 수준의 주제 검색을 결합한다. 증분 갱신을 통해 새 문서가 들어오는 환경에서도 지식 표현을 업데이트하도록 설계했다.

**우리 연구와의 관계:** 그래프 인덱싱을 자동 구축하고 dual-level 검색을 수행한다. 우리 연구는 운영 규정과 길라잡이의 기존 구간 사이에 관리자가 승인한 관계를 보존하고, 필요성이 확인된 연결 근거만 답변 컨텍스트에 추가한다.

#### 10. HippoRAG

**인용:** Bernal Jiménez Gutiérrez, Yiheng Shu, Yu Gu, Michihiro Yasunaga, and Yu Su. 2024. “HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models.” *Advances in Neural Information Processing Systems*, vol. 37. 쪽수: 확인 필요. [NeurIPS 논문 페이지](https://proceedings.neurips.cc/paper_files/paper/2024/hash/6ddc001d07ca4f319af96a3024f6dbd1-Abstract-Conference.html).

**요약:** HippoRAG는 LLM, 지식 그래프, Personalized PageRank를 결합해 여러 문서에 걸친 지식을 검색하는 구조를 제시한다. 저자들은 다중 홉 QA에서 반복 검색과 비교하고, 정확도와 비용을 평가했다.

**우리 연구와의 관계:** 자동 지식 그래프에서 연결 관계를 타고 검색한다. 우리 연구의 링크 엣지는 설비·인물 엔티티 추출 결과가 아니라 관리자가 승인한 규정·길라잡이 구간의 관계다.

#### 11. KG²RAG

**인용:** Xiangrong Zhu, Yuexiang Xie, Yi Liu, Yaliang Li, and Wei Hu. 2025. “Knowledge Graph-Guided Retrieval Augmented Generation.” In *Proceedings of NAACL 2025: Human Language Technologies, vol. 1*, pp. 8912–8924. [ACL Anthology](https://aclanthology.org/2025.naacl-long.449/), DOI: [10.18653/v1/2025.naacl-long.449](https://doi.org/10.18653/v1/2025.naacl-long.449).

**요약:** KG²RAG는 의미 검색으로 초기 문단을 찾은 뒤 지식 그래프를 사용해 관련 문단을 확장하고, 근거 문단을 구성된 순서로 배열한다. HotpotQA 기반 실험에서 검색 품질과 답변 품질을 비교했다.

**우리 연구와의 관계:** seed 기반의 질의 관련 확장이라는 점이 우리 연구와 가깝다. KG²RAG는 지식 그래프 관계를 활용하고, 우리 연구는 사람이 승인한 교차 문서 링크를 확장 경계로 쓰며 링크 유래 근거를 별도 LLM 재정렬한다.

#### 12. RAPTOR

**인용:** Parth Sarthi, Salman Abdullah, Aditi Tuli, Shubh Khanna, Anna Goldie, and Christopher Manning. 2024. “RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval.” In *International Conference on Learning Representations (ICLR 2024)*. arXiv:2401.18059. 쪽수: 확인 필요. [ICLR 논문 페이지](https://proceedings.iclr.cc/paper_files/paper/2024/hash/8a2acd174940dbca361a6398a4f9df91-Abstract-Conference.html).

**요약:** RAPTOR는 문단을 반복 군집화하고 요약해 여러 추상 수준을 가진 검색 트리를 만든다. 질의 시 원문 조각이나 상위 요약 노드를 검색해 긴 문서의 전역 맥락을 보강한다.

**우리 연구와의 관계:** 질의에 따라 필요한 계층 노드를 고르는 검색 구조라는 점에서 선택적 검색과 관련된다. RAPTOR는 문서 내부의 자동 요약 계층이며, 우리 연구의 문서 간 연결 그래프는 사람 승인 엣지로 구성된다.

### D. 사람·전문가 주석 및 규제·철도 영역 QA

#### 13. LegalBench-RAG

**인용:** Nicholas Pipitone and Ghita Houir Alami. 2024. “LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain.” arXiv preprint, arXiv:2408.10343. [arXiv](https://arxiv.org/abs/2408.10343).

**요약:** LegalBench-RAG는 법률 QA의 검색 단계를 평가하기 위해 법률 전문가가 원문에서 최소 단위의 관련 문장을 찾아 주석한 벤치마크다. 79M자 이상의 문서 코퍼스와 6,858개의 질의·응답 쌍을 제공해 큰 청크 대신 정확한 근거 구간을 회수하는 문제를 다룬다.

**우리 연구와의 관계:** 전문가가 표시한 근거 구간은 규정 조항·페이지를 평가하는 데 유사한 참고점을 준다. 해당 데이터는 정답 근거 주석이며 실행 중 탐색하는 승인 링크 그래프는 아니므로, 우리 시스템의 관리자가 승인한 구간 연결 및 선택적 확장과는 역할이 다르다.

#### 14. LegalBench

**인용:** Neel Guha et al. 2023. “LegalBench: A Collaboratively Built Benchmark for Measuring Legal Reasoning in Large Language Models.” *Advances in Neural Information Processing Systems*, vol. 36, Datasets and Benchmarks Track. 쪽수: 확인 필요. [NeurIPS 논문 페이지](https://proceedings.nips.cc/paper_files/paper/2023/hash/89e44582fd28ddfea1ea4dcb0ebbf4b0-Abstract-Datasets_and_Benchmarks.html).

**요약:** LegalBench는 법률 전문가와 연구자가 협업해 법적 추론 유형 6개를 다루는 162개 태스크를 구성했다. RAG 검색기 자체보다 LLM이 법적 규칙과 추론 과제를 처리하는 능력을 평가한다.

**우리 연구와의 관계:** 규제 분야 QA의 정답·평가 기준을 설계할 때 참고할 수 있다. 우리 연구는 모델의 법률 추론 능력보다 운영 규정 근거를 찾고 승인 링크로 연결된 특칙을 선택적으로 가져오는 retrieval 경로에 초점을 둔다.

#### 15. CARAG: 철도 운영·정비 공간 지식 그래프 RAG

**인용:** Wenkui Zheng, Mengzheng Yang, Yanfei Ren, Haoyu Wang, Chun Zeng, and Yong Zhang. 2026. “CARAG: Context-Aware Retrieval-Augmented Generation for Railway Operation and Maintenance Question Answering over Spatial Knowledge Graph.” *ISPRS International Journal of Geo-Information*, vol. 15, no. 2, Article 78. [출판사 논문 페이지](https://www.mdpi.com/2220-9964/15/2/78), DOI: [10.3390/ijgi15020078](https://doi.org/10.3390/ijgi15020078).

**요약:** CARAG는 철도 노선·운행 맥락, 운영 문서 및 정비 데이터를 개념·사례 계층의 공간 지식 그래프로 통합한다. ReAct 기반 탐색으로 질의와 관련된 공간 후보를 좁힌 뒤 벡터 검색과 그래프 검색을 적용해 철도 운영·정비 QA를 평가한다.

**우리 연구와의 관계:** 같은 철도 운영·정비 QA 영역을 다루는 가장 가까운 도메인 연구다. CARAG는 공간·개념 KG를 구성해 계층적으로 후보를 탐색하며, 우리 연구는 관리자가 승인한 문서 구간 간 링크를 따라가고 링크 근거만 별도 재정렬한다.

#### 16. 도시철도 출입문 장애 비상조치 생성

**인용:** Lu Huang, Zhigang Liu, Chengcheng Yu, Tianliang Zhu, and Bing Yan. 2026. “Emergency Operation Scheme Generation for Urban Rail Transit Train Door Systems Using Retrieval-Augmented Large Language Models.” *Sensors*, vol. 26, no. 6, Article 2006. [출판사 논문 페이지](https://www.mdpi.com/1424-8220/26/6/2006), DOI: [10.3390/s26062006](https://doi.org/10.3390/s26062006).

**요약:** 이 연구는 도시철도 출입문 장애 776건의 기록, 유지관리 규정 및 운영 매뉴얼을 통합해 비상조치안을 생성하는 RAG 시스템을 제안한다. 하이브리드 검색과 cross-encoder 재정렬, 지식 그래프 기반 고장-부품-조치 관계, 인용·절차 형식 평가를 결합한다.

**우리 연구와의 관계:** 출입문 고장 QA와 정비·운영 규정 사용이라는 면에서 도메인 직접 비교 대상이다. 해당 연구는 장애 이력과 고장 관계를 중심으로 검색하고, 우리 연구는 길라잡이와 규정 구간 사이의 승인 링크 및 연결 근거의 질문별 선택을 다룬다.

### E. RAG 평가와 LLM-as-a-judge

#### 17. RAGAS

**인용:** Shahul Es, Jithin James, Luis Espinosa Anke, and Steven Schockaert. 2024. “RAGAs: Automated Evaluation of Retrieval Augmented Generation.” In *Proceedings of EACL 2024: System Demonstrations*, pp. 150–158. [ACL Anthology](https://aclanthology.org/2024.eacl-demo.16/), DOI: [10.18653/v1/2024.eacl-demo.16](https://doi.org/10.18653/v1/2024.eacl-demo.16).

**요약:** RAGAS는 사람의 정답 주석 없이 검색 문맥의 관련성, 답변의 충실성 및 응답 품질을 평가하는 지표 모음을 제안한다. 이 구성요소별 지표는 RAG 파이프라인의 변경을 빠르게 비교하는 데 쓰인다.

**우리 연구와의 관계:** 우리 파이프라인의 faithfulness, answer relevancy, context precision/recall 평가와 직접 연결된다. 링크 확장의 기여를 보일 때 전체 응답 점수 외에 링크 유래 근거의 적중률과 불필요한 확장 비율도 함께 분리해 보고할 필요가 있다.

#### 18. ARES

**인용:** Jon Saad-Falcon, Omar Khattab, Christopher Potts, and Matei Zaharia. 2024. “ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems.” In *Proceedings of NAACL-HLT 2024, vol. 1*, pp. 338–354. [ACL Anthology](https://aclanthology.org/2024.naacl-long.20/), DOI: [10.18653/v1/2024.naacl-long.20](https://doi.org/10.18653/v1/2024.naacl-long.20).

**요약:** ARES는 synthetic training data로 경량 LM judge를 학습해 문맥 관련성, 답변 충실성, 답변 관련성을 자동 평가한다. 평가 오류를 줄이기 위해 소량의 사람 주석을 prediction-powered inference에 활용한다.

**우리 연구와의 관계:** 자동 점수와 소수 전문가 검토를 함께 사용하는 평가 방법으로 참고할 수 있다. 우리 연구의 핵심 비교에서는 사람이 확인한 정답 근거 라벨을 유지하고, LLM judge 점수는 보조 지표로 취급하는 편이 타당하다.

#### 19. LLM-as-a-judge의 편향

**인용:** Lianmin Zheng et al. 2023. “Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.” *Advances in Neural Information Processing Systems*, vol. 36, Datasets and Benchmarks Track. arXiv:2306.05685. 쪽수: 확인 필요. [NeurIPS 논문 페이지](https://papers.neurips.cc/paper_files/paper/2023/hash/91f18a1287b398d378ef22505bf41832-Abstract-Datasets_and_Benchmarks.html).

**요약:** 이 연구는 LLM judge가 사람 선호를 얼마나 재현하는지 평가하고 위치 편향, 장황함 편향, 자기 강화 편향을 분석한다. GPT-4 judge의 사람 선호 일치도는 높을 수 있지만, 프롬프트와 비교 순서에 따른 취약성도 보고한다.

**우리 연구와의 관계:** LLM 재정렬 및 자동 점수에 대한 신뢰 한계를 설명한다. 철도 안전 규정의 확장 근거 선택은 단일 자동 점수로 결론내리지 말고, 정답 근거와 링크 적합성의 사람 검토를 통해 보완한다.

#### 20. RAGChecker

**인용:** Dongyu Ru et al. 2024. “RAGChecker: A Fine-grained Framework for Diagnosing Retrieval-Augmented Generation.” arXiv preprint, arXiv:2408.08067. [arXiv](https://arxiv.org/abs/2408.08067).

**요약:** RAGChecker는 retrieval과 generation을 각각 진단하는 세분화된 RAG 지표를 제안하고, 사람 판단과의 상관을 평가한다. 여러 시스템을 분석해 검색 누락, 근거 잡음 및 생성 문제를 분리해서 볼 수 있도록 한다.

**우리 연구와의 관계:** selective expansion을 검증할 때 검색 단계 개선과 생성 단계 개선을 나눠 분석하는 데 도움이 된다. 특히 직접 근거와 링크 경유 근거를 구분해 회수율·정밀도 변화를 보고하면 기여의 원인을 더 명확히 할 수 있다.

### F. 생성 답변의 인용·출처 귀속

#### 21. ALCE

**인용:** Tianyu Gao, Howard Yen, Jiatong Yu, and Danqi Chen. 2023. “Enabling Large Language Models to Generate Text with Citations.” In *Proceedings of EMNLP 2023*, pp. 6465–6488. [ACL Anthology](https://aclanthology.org/2023.emnlp-main.398/), DOI: [10.18653/v1/2023.emnlp-main.398](https://doi.org/10.18653/v1/2023.emnlp-main.398).

**요약:** ALCE는 근거를 검색해 답변을 만들고 인용하는 end-to-end 시스템을 비교하는 자동 인용 평가 벤치마크다. 유창성, 정답성, 인용 품질 지표를 제안하고 기존 모델이 문장 전체를 뒷받침하는 인용을 자주 누락함을 보였다.

**우리 연구와의 관계:** 답변 문장과 규정 근거를 연결해 인용 정확도를 평가한다는 점에서 직접 관련된다. 우리 시스템은 근거 번호를 생성한 뒤 실제 문장 내용과 근거의 일치도를 보정하므로, 링크에서 온 특칙의 인용까지 별도로 점검할 수 있다.

#### 22. FActScore

**인용:** Sewon Min, Kalpesh Krishna, Xinxi Lyu, Mike Lewis, Wen-tau Yih, Pang Koh, Mohit Iyyer, Luke Zettlemoyer, and Hannaneh Hajishirzi. 2023. “FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation.” In *Proceedings of EMNLP 2023*, pp. 12076–12100. [ACL Anthology](https://aclanthology.org/2023.emnlp-main.741/), DOI: [10.18653/v1/2023.emnlp-main.741](https://doi.org/10.18653/v1/2023.emnlp-main.741).

**요약:** FActScore는 긴 생성 답변을 원자적 사실 단위로 나누고, 각 사실이 신뢰 가능한 지식원에 의해 뒷받침되는 비율을 계산한다. 사람 평가 자료와 retrieval·LLM을 이용한 자동 평가기를 비교한다.

**우리 연구와의 관계:** 절차형 답변의 주체·조건·순서·수치별 근거 충실도를 점검하는 데 참고된다. 문장 전체의 유사도뿐 아니라 각 조치 사실이 직접 규정 또는 승인 링크 경유 규정 중 어느 근거로 뒷받침되는지 분해해서 평가할 수 있다.

#### 23. 교차 언어 QA의 출처 귀속

**인용:** Benjamin Muller, John Wieting, Jonathan H. Clark, Tom Kwiatkowski, Sebastian Ruder, Livio Baldini Soares, Roee Aharoni, Jonathan Herzig, and Xinyi Wang. 2023. “Evaluating and Modeling Attribution for Cross-Lingual Question Answering.” In *Proceedings of EMNLP 2023*, pp. 144–157. [ACL Anthology](https://aclanthology.org/2023.emnlp-main.10/), DOI: [10.18653/v1/2023.emnlp-main.10](https://doi.org/10.18653/v1/2023.emnlp-main.10).

**요약:** 이 연구는 다국어 QA에서 모델 답변이 검색된 passage에 실제로 귀속되는 정도를 측정하는 XOR-AttriQA 데이터셋을 제시한다. 정답 문자열이 맞더라도 검색 근거에 귀속되지 않는 응답이 적지 않음을 보이고 귀속 탐지 방법을 비교한다.

**우리 연구와의 관계:** 출처 제시와 실제 근거 사용을 구분한다는 점에서 인용 보정 및 근거 검증의 배경 연구다. 우리 연구는 노선·업무 문서 간 링크를 명시적으로 추적해 답변의 근거 경로를 관리한다.

### G. 한국 국내 연구

#### 24. 한국어 법률 QA 하이브리드 RAG

**인용:** 서준원, 민정혜. 2025. “한국어 법률 QA를 위한 하이브리드 RAG 시스템 최적화.” *한국컴퓨터정보학회논문지*, 제30권, 제8호, pp. 53–63. [KCI 논문 페이지](https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART003234187), DOI: [10.9708/jksci.2025.30.08.053](https://doi.org/10.9708/jksci.2025.30.08.053).

**요약:** 의미 기반 청킹, 한국 법률 데이터로 fine-tuning한 E5 임베딩, BM25 조합을 비교해 한국어 법률 QA를 위한 하이브리드 검색을 평가한다. 해당 조합이 비교 실험의 검색 정확도와 응답 사실성에서 가장 나은 결과를 보였다고 보고한다.

**우리 연구와의 관계:** 한국어 규정 문서 QA와 hybrid retrieval이라는 직접 비교 기준이다. 해당 연구는 chunking·embedding·검색 융합을 최적화하며, 우리 연구는 사람이 승인한 문서 간 링크를 통해 특칙 근거를 선택적으로 확장한다.

#### 25. 한국어 의료 QA RAG

**인용:** 김나랑. 2025. “LLM 기반 검색 증강 생성 구조를 활용한 한국어 의료 질의응답 시스템 연구.” *e-비즈니스연구*, 제26권, 제2호, pp. 41–55. [KCI 논문 페이지](https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART003201002), DOI: [10.20462/tebs.2025.4.26.2.41](https://doi.org/10.20462/tebs.2025.4.26.2.41).

**요약:** 서울대학교병원이 제공하는 질병 정의 데이터로 한국어 의료 지식베이스를 구성하고 RAG 적용·미적용 QA를 비교한다. GPT-3.5 Turbo, GPT-4o, LLaMA 2 7B 등의 응답을 BLEU·정확도·F1 등으로 평가했다.

**우리 연구와의 관계:** 한국어 고위험 전문 영역에서 외부 공식 지식으로 답변을 grounding하는 비교 사례다. 이 연구는 의료 지식베이스를 검색해 답하지만, 우리 연구는 운영 규정·길라잡이의 승인된 구간 연결로 링크 경유 특칙을 확인한다.

#### 26. 국방 법령 QA를 위한 공개 한국어 LLM

**인용:** 전진호, 박순태, 한충희, 이소울, 김경백. 2025. “공개 한국어 언어모델의 국방 도메인 파인튜닝 가능성 연구.” *국방과 보안*, 제7권, 제2호, pp. 234–256. [KCI 논문 페이지](https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART003276381), DOI: [10.23425/defsec.2025.7.2.234](https://doi.org/10.23425/defsec.2025.7.2.234).

**요약:** 공개 법령·훈령으로 3,199개 질의응답 데이터를 만들고 19개 공개 한국어 LLM의 국방 도메인 fine-tuning을 평가한다. 논문은 공개 법령 기반 내부 모델의 가능성과 함께 향후 RAG·보안 배포를 연구 과제로 언급한다.

**우리 연구와의 관계:** 법령·규정의 보안성과 정확도가 중요한 국내 도메인 QA 사례다. 모델 fine-tuning 중심 연구와 달리, 우리 연구는 데이터의 문서 간 관계를 사람이 승인하고 질문에 맞는 연결 근거만 검색해 제공한다.

#### 27. 철도 보고서 문서의 RAG 청킹

**인용:** 임지수, 원종운. 2025. “보고서 형식 문서에 적합한 RAG 기반 청킹 전략에 관한 연구.” *2025년도 대한전자공학회 하계학술대회 논문집*, p. 5108. [DBpia 논문 페이지](https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE12332702).

**요약:** 철도 관련 보고서 52건의 장·절 구조와 표·항목 정보를 고려해 문서 파싱과 청크 크기를 비교한다. 고정 길이와 겹침 크기의 조합을 실험해 철도 보고서 기반 RAG의 검색 품질을 다룬다.

**우리 연구와의 관계:** 국내 철도 문서를 대상으로 한 RAG 연구로, 도메인 용어와 문서 구조를 보존하는 전처리 비교에 유용하다. 우리 연구는 청킹 설계 외에 규정·길라잡이 사이의 승인 링크와 링크 근거의 선택을 다룬다.

#### 28. 한국철도학회 프로그램: Graph RAG 기반 사고 요인 분석

**인용:** 김대혁, 이범우, 나정현, 차효정, 박준태, 서준수. 2026. “Graph RAG 기반 철도 유지관리 기술 고도화를 위한 사고 요인 분석 방안.” *2026 한국철도학회 춘계학술대회* 공식 프로그램, 발표번호 KSR2026S112. 논문집 쪽수·전문 공개 여부: 확인 필요. [한국철도학회 프로그램](https://railway.or.kr/Papers_Conference/202607/sub6.html).

**요약:** 학회 공식 프로그램에는 철도 유지관리의 사고 요인 분석을 Graph RAG로 다루는 발표가 제목과 저자, 발표번호와 함께 등재되어 있다. 확인 가능한 프로그램 페이지에는 그래프 구축 방법과 실험 결과가 공개되어 있지 않다.

**우리 연구와의 관계:** 국내 철도 Graph RAG가 유지관리 영역으로 확장되고 있음을 보여주는 최신 프로그램 기록이다. 구성·확장 정책은 원문 확인 전까지 분류하지 않으며, 우리 연구와의 차이는 논문 전문 및 발표 자료 검토 후 확정해야 한다.

#### 29. 한국철도학회 프로그램: 철도차량 출입문 정비 RAG

**인용:** 김정태, 김철수. 2026. “RAG 기반 철도차량 출입문장치 정비 지원 시스템 개발.” *2026 한국철도학회 춘계학술대회* 공식 프로그램, 발표번호 KSR2026S121. 논문집 쪽수·전문 공개 여부: 확인 필요. [한국철도학회 프로그램](https://railway.or.kr/Papers_Conference/202607/sub6.html).

**요약:** 공식 프로그램은 철도차량 출입문장치 정비 지원에 RAG를 적용한 발표의 제목과 발표자를 확인해 준다. 공개 프로그램만으로 검색 방식, 그래프 여부, 성능 평가 결과는 확인할 수 없다.

**우리 연구와의 관계:** 출입문 장애·정비와 RAG라는 국내 도메인 인접 사례다. 우리 연구의 승인 링크 및 선택 확장과의 차이는 전문 또는 발표 자료가 확인될 때까지 미정으로 둔다.

#### 30. 한국노동패널 KLIPS 지식 챗봇

**인용:** 민인식. 2025. “RAG-LLM 기반 KLIPS 지식 챗봇 개발.” *노동정책연구*, 제25권, 제3호, pp. 139–164. [KCI 논문 페이지](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003249123), DOI: [10.22914/jlp.2025.25.3.006](https://doi.org/10.22914/jlp.2025.25.3.006).

**요약:** 한국노동패널 공식 문헌을 지식베이스로 구성하고 한국어 특화 EXAONE 4.0 기반 RAG 챗봇을 개발해 글로벌 LLM과 비교한다. KLIPS 고유 용어의 재현과 환각 억제에서 RAG-EXAONE의 결과를 보고하며 인간-AI 협업 방식의 지식베이스 개선을 제안한다.

**우리 연구와의 관계:** 국내 공식 문서 기반의 도메인 특화 RAG 사례이며, 사람과 지식베이스 개선을 연결한다. 우리 연구는 문서 내용의 공동 구축보다 관리자가 승인한 교차 문서 링크를 검색 때 적용하는 데 초점을 둔다.

## 종합 및 연구 위치

### 그래프 구성·확장 방식 비교

| 연구 계열 | 그래프·관계 구성 | 확장 및 선택 | 대상 영역 |
|---|---|---|---|
| Lewis RAG, DPR, sparse+dense hybrid, LLM reranking | 그래프 없음. 문서·문단을 검색 단위로 사용 | 순위 기반 top-k 검색·재정렬 | 일반 지식 QA 및 정보검색 |
| Microsoft GraphRAG, LightRAG, HippoRAG | LLM 기반 엔티티·관계 추출 및 자동 그래프/커뮤니티 구성 | 질의에 따른 로컬·전역·PPR 탐색 | 일반 문서 집합 |
| KG²RAG | 문서에서 관계 그래프를 구성해 seed 문단과 연결 | seed 검색 후 그래프 유도 문단 확장·정렬 | 다중 홉 QA |
| RAPTOR | 자동 요약·군집화 트리, 명시적 문서 링크 그래프는 아님 | 질의에 맞춰 원문 또는 요약 계층 선택 | 장문 문서 QA |
| CARAG, 도시철도 출입문 RAG | 공간 데이터·구조화 기록·고장 관계 기반 도메인 그래프 | 질의·공간·장애 맥락으로 후보를 줄인 뒤 문서·그래프 검색 | 철도 운영·정비 |
| LegalBench-RAG, LegalBench | 전문가가 관련 근거 구간 또는 평가 태스크를 주석 | 평가용 정답 근거·태스크, 런타임 링크 확장은 없음 | 법률 |
| 한국철도학회 2026 프로그램 기록 | 전문 확인 전에는 구성 방식 미상 | 전문 확인 전에는 선택 정책 미상 | 철도 유지관리·출입문 정비 |
| **본 연구** | **관리자가 승인한 규정·길라잡이 구간 간 문서 링크** | **직접 검색 결과를 유지하고, 승인 링크를 최대 2 hop 따라간 뒤 연결 근거만 LLM 재정렬; 무관한 연결 근거는 제외** | **서울 6호선 운전·정비 규정 QA** |

GraphRAG·LightRAG·HippoRAG 계열은 관계 지식을 자동 구축해 그래프 수준의 연관성이나 전역 주제를 탐색한다. LegalBench-RAG는 사람이 법률 근거를 정밀하게 주석하지만 그 주석은 벤치마크의 gold span으로 사용된다. CARAG와 도시철도 출입문 연구는 철도 운영·정비 데이터에 구조화된 그래프와 검색을 적용해 도메인 연관성이 높다. 본 연구의 구별점은 관리자가 승인한 구간 간 관계를 검색 그래프의 엣지로 유지하고, 링크가 존재하는 모든 구간을 넣지 않고 질문과의 관련성을 다시 평가해 답변에 포함하는 데 있다.

### 3쪽 논문에 우선 인용할 12편

추천 문헌은 [references.md](references.md)에 KIISE 형식으로 정리했다. RAG 기본 구조와 DPR, sparse-dense 검색, LLM 재정렬, 자동 그래프 RAG와 Human-annotated LegalBench-RAG, RAG 평가·인용, 한국어 법률·철도 문서 연구를 포함했다. 한국철도학회 프로그램의 두 항목은 전문이 확인되지 않아 우선 인용 목록에서 제외했다.
