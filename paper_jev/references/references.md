# 참고문헌

아래 서지 정보와 링크는 2026-10-17에 웹 검색으로 확인했다. 학술 서지는 ACL Anthology, PMLR, arXiv 및 DOI 출판사 기록을 우선 사용했다. 각 항목의 관련성은 본 연구에서 사용할 맥락을 설명하며, 해당 연구의 결과가 본 연구의 결과를 보장한다는 뜻은 아니다.

[1] P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Küttler, M. Lewis, W. Yih, T. Rocktäschel, S. Riedel, and D. Kiela, “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” *Advances in Neural Information Processing Systems*, vol. 33, pp. 9459–9474, 2020. [NeurIPS](https://papers.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html), [arXiv:2005.11401](https://arxiv.org/abs/2005.11401).

관련성: 검색된 근거를 생성 모델에 제공하는 RAG의 기본 배경이다.

[2] D. Edge, H. Trinh, N. Cheng, J. Bradley, A. Chao, A. Mody, S. Truitt, D. Metropolitansky, R. O. Ness, and J. Larson, “From Local to Global: A Graph RAG Approach to Query-Focused Summarization,” arXiv:2404.16130, 2024. [arXiv](https://arxiv.org/abs/2404.16130), [Microsoft GraphRAG documentation](https://microsoft.github.io/graphrag/).

관련성: LLM으로 엔터티 그래프와 커뮤니티 요약을 구성하는 대표 GraphRAG 접근으로, 본 연구의 그래프 구성 비용 문제와 비교 기준을 제공한다.

[3] Z. Guo, L. Xia, Y. Yu, T. Ao, and C. Huang, “LightRAG: Simple and Fast Retrieval-Augmented Generation,” in *Findings of the Association for Computational Linguistics: EMNLP 2025*, pp. 10746–10761, 2025. doi: [10.18653/v1/2025.findings-emnlp.568](https://doi.org/10.18653/v1/2025.findings-emnlp.568).

관련성: 그래프 구조와 벡터 표현을 결합하는 RAG 시스템의 예로, 링크 구성과 검색 확장을 구분해 설명하는 데 쓴다.

[4] X. Zhu, Y. Xie, Y. Liu, Y. Li, and W. Hu, “Knowledge Graph-Guided Retrieval Augmented Generation,” in *Proceedings of NAACL-HLT 2025*, pp. 8912–8924, 2025. doi: [10.18653/v1/2025.naacl-long.449](https://doi.org/10.18653/v1/2025.naacl-long.449).

관련성: seed chunk에서 그래프를 따라 관련 chunk를 확장하는 방식으로, 기존 링크를 검색에 쓰는 본 시스템과 연결된다.

[5] Y. Hu, Z. Lei, Z. Zhang, B. Pan, C. Ling, and L. Zhao, “GRAG: Graph Retrieval-Augmented Generation,” in *Findings of the Association for Computational Linguistics: NAACL 2025*, pp. 4145–4157, 2025. doi: [10.18653/v1/2025.findings-naacl.232](https://doi.org/10.18653/v1/2025.findings-naacl.232).

관련성: 인용 그래프 등 네트워크형 문서에서 텍스트 하위 그래프를 검색하는 접근으로, 문서 간 연결의 중요성을 뒷받침한다.

[6] C. Min, R. Mathew, J. Pan, S. Bansal, A. Keshavarzi, and A. V. Kannan, “Efficient Knowledge Graph Construction and Retrieval from Unstructured Text for Large-Scale RAG Systems,” arXiv:2507.03226, 2025. [arXiv](https://arxiv.org/abs/2507.03226).

관련성: 의존 구문 분석으로 LLM을 쓰지 않고 엔터티·관계 그래프를 만드는 비용 효율 접근을 직접 비교한다. 결과는 SAP 코드 마이그레이션 자료에 대한 것이므로 규정 QA 결과로 일반화하지 않는다.

[7] Y. Yao et al., “DocRED: A Large-Scale Document-Level Relation Extraction Dataset,” in *Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics*, pp. 764–777, 2019. doi: [10.18653/v1/P19-1074](https://doi.org/10.18653/v1/P19-1074).

관련성: 문서 여러 문장에 걸친 관계 추출이 단일 문장 분류와 다를 수 있음을 보여주는 데이터셋·과제 정의다.

[8] G. Li, P. Wang, and W. Ke, “Revisiting Large Language Models as Zero-shot Relation Extractors,” in *Findings of the Association for Computational Linguistics: EMNLP 2023*, pp. 6877–6892, 2023. [ACL Anthology](https://aclanthology.org/2023.findings-emnlp.459/).

관련성: zero-shot LLM 관계 추출의 장점과 관계별 성능 편차를 보고해, 링크 판정에서 관계 유형과 거절 사례를 따로 살펴볼 이유를 제공한다.

[9] Z. Wan, F. Cheng, Z. Mao, Q. Liu, H. Song, J. Li, and S. Kurohashi, “GPT-RE: In-context Learning for Relation Extraction using Large Language Models,” in *Proceedings of EMNLP 2023*, pp. 3534–3547, 2023. doi: [10.18653/v1/2023.emnlp-main.214](https://doi.org/10.18653/v1/2023.emnlp-main.214).

관련성: 예시 검색과 설명을 이용해 LLM의 관계 추출을 개선하며, null 관계의 오분류 문제도 논의한다.

[10] L. Zheng et al., “Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena,” arXiv:2306.05685, 2023. [arXiv](https://arxiv.org/abs/2306.05685).

관련성: 자동 judge의 사람 평가 일치 가능성과 위치·장문 선호 등 편향을 함께 분석해, 자동 점수를 보조 평가로 제한하는 근거가 된다.

[11] S. Es, J. James, L. Espinosa Anke, and S. Schockaert, “RAGAs: Automated Evaluation of Retrieval Augmented Generation,” in *Proceedings of EACL 2024: System Demonstrations*, pp. 150–158, 2024. doi: [10.18653/v1/2024.eacl-demo.16](https://doi.org/10.18653/v1/2024.eacl-demo.16).

관련성: 검색 문맥과 생성 응답의 여러 자동 평가 차원을 정리해 RAG 결과 평가의 배경을 제공한다.

[12] C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, “On Calibration of Modern Neural Networks,” in *Proceedings of the 34th International Conference on Machine Learning*, PMLR 70, pp. 1321–1330, 2017. [PMLR](https://proceedings.mlr.press/v70/guo17a.html).

관련성: ECE와 reliability diagram 등 예측 확률 보정 평가의 기준이 된다.

[13] S. Kadavath et al., “Language Models (Mostly) Know What They Know,” arXiv:2207.05221, 2022. [arXiv](https://arxiv.org/abs/2207.05221).

관련성: 언어 모델의 자기 평가 확률을 조사하고 과제 간 확률 보정의 한계를 보여, Jev와 LLM confidence를 별도 보정 지표로 비교하도록 뒷받침한다.

[14] L. Chen, M. Zaharia, and J. Zou, “FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance,” arXiv:2305.05176, 2023. [arXiv](https://arxiv.org/abs/2305.05176).

관련성: 비용 절감을 위해 모델을 cascade로 조합하는 접근으로, 불확실한 링크만 고비용 판단으로 넘기는 운영 방향과 연관된다.

[15] I. Ong, A. Almahairi, V. Wu, W.-L. Chiang, T. Wu, J. E. Gonzalez, M. W. Kadous, and I. Stoica, “RouteLLM: Learning to Route LLMs with Preference Data,” in *International Conference on Learning Representations*, 2025. [OpenReview](https://openreview.net/forum?id=8sSqNntaMr), [arXiv:2406.18665](https://arxiv.org/abs/2406.18665).

관련성: 질의별로 강한 모델과 저렴한 모델을 선택하는 학습 기반 라우팅 연구로, 본 연구의 단가·품질 비교가 비용 최적화 논의와 만나는 지점이다.

[16] N. Sannier, M. Adedjouma, M. Sabetzadeh, and L. Briand, “An Automated Framework for Detection and Resolution of Cross References in Legal Texts,” *Requirements Engineering*, vol. 22, no. 2, pp. 215–237, 2017. doi: [10.1007/s00766-015-0241-3](https://doi.org/10.1007/s00766-015-0241-3).

관련성: 문서 구조와 자연어 패턴으로 법률 상호참조를 감지하고 조항에 연결하는 연구로, 규정 링크의 정확한 대상 해소와 근거 추적을 위한 도메인 배경이다.

[17] O. T. Tran et al., “Reference Resolution in Legal Texts,” in *Proceedings of the 14th International Conference on Artificial Intelligence and Law*, pp. 101–110, 2013. doi: [10.1145/2514601.2514613](https://doi.org/10.1145/2514601.2514613).

관련성: 법률 문서에서 참조 표현을 탐지하고 대상 텍스트로 해소하는 단계별 방법을 제시한다. 본 연구는 명시적 참조 외의 의미 기반 문서 간 링크도 다룬다.

[18] D. Almeida, “Introducing System One Models & Jev,” TypeSafe AI, company blog. [TypeSafe](https://typesafe.ai/blog/introducing-system-one-models-and-jev).

관련성: Jev와 System One의 개발사 설명 및 제품 주장을 원 출처로 확인한다. 속도·효율·보정에 관한 설명은 독립 실험 결과가 아닌 공급자 주장으로 취급한다.

[19] TypeSafe AI, “System One API documentation,” [llms.txt](https://docs.typesafe.ai/llms.txt) and [API reference](https://api.typesafe.ai/redoc).

관련성: `choice`, `score` 등 구조화 판단 요청과 확률 응답의 API 계약을 확인하는 1차 문서다. API 문서는 제품 인터페이스 자료이며 학술적 비교 평가가 아니다.
