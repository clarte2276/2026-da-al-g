# Dense retrieval diagnostic

Retrieval was rerun through `GraphRAGService.retrieve` for dense and hybrid, with `top_k=10` and graph hops disabled. The shared SQLite path uses the full corpus for both variants.

## vehicle_failure

**Question:** 열차 운전 중 차량고장으로 자력운전이 곤란하면 어떤 조치를 해야 하나요?

**Gold evidence:** `[{"document_version_id": "35315ef6-c82f-44fd-904c-62b78bdc474a", "article": 326, "page": null, "label": "운전취급규정 제326조", "via_link": false}]`

**Corpus:** 4288 units; `vectors.shape=(4288, 1536)`; query dimension 1536; nonzero dense scores 4288.

| Variant | Rank | Fragment ID | Document | Article / location | Dense score | BM25 score | Retrieval score | Gold match |
|---|---:|---|---|---|---:|---:|---:|:---:|
| dense | 1 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제348조:106024` | 운전취급규정.hwp | 제348조 | 0.534324 | 0.126336 | 0.534324 | no |
| dense | 2 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제349조:106138` | 운전취급규정.hwp | 제349조 | 0.534324 | 0.188697 | 0.534324 | no |
| dense | 3 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제15조:3540` | 운전취급규정.hwp | 제15조 | 0.511470 | 0.056198 | 0.511470 | no |
| dense | 4 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제16조:3832` | 운전취급규정.hwp | 제16조 | 0.511470 | 0.056198 | 0.511470 | no |
| dense | 5 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제17조:3920` | 운전취급규정.hwp | 제17조 | 0.511470 | 0.040770 | 0.511470 | no |
| dense | 6 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제18조:4026` | 운전취급규정.hwp | 제18조 | 0.511470 | 0.040770 | 0.511470 | no |
| dense | 7 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제19조:4143` | 운전취급규정.hwp | 제19조 | 0.511470 | 0.040770 | 0.511470 | no |
| dense | 8 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제20조:4562` | 운전취급규정.hwp | 제20조 | 0.511470 | 0.000000 | 0.511470 | no |
| dense | 9 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제21조:4643` | 운전취급규정.hwp | 제21조 | 0.511470 | 0.086780 | 0.511470 | no |
| dense | 10 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제22조:4714` | 운전취급규정.hwp | 제22조 | 0.511470 | 0.040770 | 0.511470 | no |
| hybrid | 1 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제326조:99018` | 운전취급규정.hwp | 제326조 | 0.482131 | 0.386747 | 0.443977 | yes |
| hybrid | 2 | `7a18c868-c6ad-4708-8564-fe5ccb36444c:article:제54조:5` | 관제업무내규.hwp | 제54조 | 0.451396 | 0.369329 | 0.418569 | no |
| hybrid | 3 | `df60a06c-71bf-49cc-8b93-bde500b5436c:article:제54조:15877` | 관제업무내규.hwp | 제54조 | 0.439888 | 0.369329 | 0.411664 | no |
| hybrid | 4 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제30조:6532` | 운전취급규정.hwp | 제30조 | 0.455196 | 0.338085 | 0.408351 | no |
| hybrid | 5 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제349조:106138` | 운전취급규정.hwp | 제349조 | 0.534324 | 0.188697 | 0.396073 | no |
| hybrid | 6 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제348조:106024` | 운전취급규정.hwp | 제348조 | 0.534324 | 0.126336 | 0.371129 | no |
| hybrid | 7 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제336조:101813` | 운전취급규정.hwp | 제336조 | 0.452803 | 0.235660 | 0.365946 | no |
| hybrid | 8 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제327조:99182` | 운전취급규정.hwp | 제327조 | 0.482131 | 0.189650 | 0.365139 | no |
| hybrid | 9 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제62조:14700` | 운전취급규정.hwp | 제62조 | 0.482833 | 0.166869 | 0.356448 | no |
| hybrid | 10 | `c6ce2457-3620-4089-909d-d616458da7f5:article:제122조:100510` | 안전관리체계관리규정.hwp | 제122조 | 0.451230 | 0.204177 | 0.352409 | no |

## brake_pipe

**Question:** 정거장 외에서 제동관 또는 공기관 고장으로 통기불능이면 구원과 운전을 어떻게 처리하나요?

**Gold evidence:** `[{"document_version_id": "35315ef6-c82f-44fd-904c-62b78bdc474a", "article": 327, "page": null, "label": "운전취급규정 제327조", "via_link": false}]`

**Corpus:** 4288 units; `vectors.shape=(4288, 1536)`; query dimension 1536; nonzero dense scores 4288.

| Variant | Rank | Fragment ID | Document | Article / location | Dense score | BM25 score | Retrieval score | Gold match |
|---|---:|---|---|---|---:|---:|---:|:---:|
| dense | 1 | `1641ee66-3d5f-4681-b5fb-5f787be57764` | 6호선 전동차고장조치 길라잡이-1.pptx | 슬라이드 27 · 비상제동 풀림불능 시 구원운전 방법 | 0.531433 | 0.144015 | 0.531433 | no |
| dense | 2 | `3c80bea5-7a8a-46ba-a5f8-28414307ac09` | 6호선 전동차고장조치 길라잡이-2.pptx | 슬라이드 22 · 전 차량 역행불능 시 | 0.514654 | 0.049709 | 0.514654 | no |
| dense | 3 | `5439243f-cbe3-4588-9cd5-86c877851c0e` | 6호선 전동차고장조치 길라잡이-1.pptx | 슬라이드 66 | 0.496359 | 0.049709 | 0.496359 | no |
| dense | 4 | `8743031a-6518-454a-9779-9eb3d9cfcfad` | 6호선 전동차고장조치 길라잡이-2.pptx | 슬라이드 1 | 0.496359 | 0.049709 | 0.496359 | no |
| dense | 5 | `1a55a6c0-b6d4-4025-bee3-1cfeb894d376` | 6호선 전동차고장조치 길라잡이-1.pptx | 슬라이드 30 | 0.492689 | 0.049709 | 0.492689 | no |
| dense | 6 | `5b979a14-1f49-4499-9e0e-ca28da18f0e9:article:제75조:18957` | 차량기지운전취급내규.hwp | 제75조 | 0.487387 | 0.068784 | 0.487387 | no |
| dense | 7 | `5b979a14-1f49-4499-9e0e-ca28da18f0e9:article:제76조:19041` | 차량기지운전취급내규.hwp | 제76조 | 0.487387 | 0.060258 | 0.487387 | no |
| dense | 8 | `5b979a14-1f49-4499-9e0e-ca28da18f0e9:article:제77조:19282` | 차량기지운전취급내규.hwp | 제77조 | 0.487387 | 0.050251 | 0.487387 | no |
| dense | 9 | `5b979a14-1f49-4499-9e0e-ca28da18f0e9:article:제78조:20369` | 차량기지운전취급내규.hwp | 제78조 | 0.487387 | 0.019076 | 0.487387 | no |
| dense | 10 | `5b979a14-1f49-4499-9e0e-ca28da18f0e9:article:제79조:20472` | 차량기지운전취급내규.hwp | 제79조 | 0.487387 | 0.049709 | 0.487387 | no |
| hybrid | 1 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제327조:99182` | 운전취급규정.hwp | 제327조 | 0.463672 | 0.633260 | 0.531507 | yes |
| hybrid | 2 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제315조:95972` | 운전취급규정.hwp | 제315조 | 0.441618 | 0.415849 | 0.431310 | no |
| hybrid | 3 | `1641ee66-3d5f-4681-b5fb-5f787be57764` | 6호선 전동차고장조치 길라잡이-1.pptx | 슬라이드 27 · 비상제동 풀림불능 시 구원운전 방법 | 0.531433 | 0.144015 | 0.376466 | no |
| hybrid | 4 | `4116526b-b97e-48a2-b76a-2050eb838bdc:article:제79조:40165` | 운전관계직원업무내규.hwp | 제79조 | 0.462917 | 0.214250 | 0.363450 | no |
| hybrid | 5 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제304조:92213` | 운전취급규정.hwp | 제304조 | 0.445544 | 0.198051 | 0.346546 | no |
| hybrid | 6 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제67조:18290` | 운전취급규정.hwp | 제67조 | 0.448542 | 0.187464 | 0.344111 | no |
| hybrid | 7 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제336조:101813` | 운전취급규정.hwp | 제336조 | 0.428120 | 0.217089 | 0.343708 | no |
| hybrid | 8 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제347조:105048` | 운전취급규정.hwp | 제347조 | 0.460748 | 0.166859 | 0.343192 | no |
| hybrid | 9 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제330조:100014` | 운전취급규정.hwp | 제330조 | 0.463672 | 0.160624 | 0.342453 | no |
| hybrid | 10 | `35315ef6-c82f-44fd-904c-62b78bdc474a:article:제326조:99018` | 운전취급규정.hwp | 제326조 | 0.463672 | 0.156831 | 0.340936 | no |

## Finding

For both cases, the stored corpus has 4,288 vectors of dimension 1,536, the query dimension matches, and all 4,288 dense scores are nonzero. Dense top-10 does not include either gold article; hybrid ranks each exact gold version/article first. This is a dense retrieval-ranking failure on these examples, not missing vectors or an evaluation-side ID mismatch.

Article units inherit their parent chunk embedding. As a result, neighboring articles can have identical dense scores: for example, articles 15–22 all score 0.511470 for `vehicle_failure`. Dense-only retrieval cannot discriminate between those articles from their vectors; hybrid recovers the exact gold articles through BM25 (article 326 for `vehicle_failure`, article 327 for `brake_pipe`). This is a property of the baseline representation, not a missing-vector or evaluation bug.
