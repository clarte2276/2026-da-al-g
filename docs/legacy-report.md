# 레거시 레포지토리(`2026-da-al-g_legacy`) 기능 정리 보고서

> 대상: `2026-da-al-g_legacy` 레포지토리 전체
> 목적: 신규 레포(`2026-da-al-g`)로 이관하기 전, 레거시에서 실제로 제공되던 기능을 화면·API·데이터 단위로 기록
> 작성일: 2026-08-18

## 0. 레포 구조 요약

| 디렉토리 | 역할 |
|---|---|
| `app/` | Flutter 클라이언트 (규정/근무 보조 앱, 이름: `DaAlJiApp` / "DA-AL-JI") |
| `back/` | FastAPI 진입점 (`main.py`). 실제 앱 객체는 `ai.api`에서 로드하도록 되어 있음 |
| `ai/` | **현재 완전히 비어 있음.** git 이력상 백엔드 소스가 이 경로에서 전부 삭제된 상태 — 이관/재작성 진행 중으로 추정 |
| `ai_legacy/` | `ai/`가 비기 전의 백엔드 실제 구현 전체 (인증, RAG 검색, 규정/근무 API). 이 보고서의 백엔드 파트는 이 코드를 근거로 작성 |
| `data/` | 규정 원문, 근무계획 엑셀, "길라잡이"(전동차 고장조치 매뉴얼) 등 RAG 소스 코퍼스 |
| `tools/` | HWP/PPTX/XLSX 원본을 RAG용 마크다운·JSON으로 변환하는 전처리 스크립트 |
| `docs/` | 발표자료, 부속 파일 조사 문서 등 |
| `temp/` | 변환 백업, 임시 이미지 |

**주의**: `back/main.py`는 `from ai.api import app`으로 앱을 로드하는데 현재 `ai/`가 비어 있어 그대로는 서버가 기동되지 않는다. 정상 동작하려면 `ai_legacy/`의 내용을 `ai/`로 옮기거나 import 경로를 수정해야 한다.

---

## 1. Flutter 앱 (`app/`)

### 1.1 개요

- Flutter (SDK `^3.11.4`), Material 3 기반 단일 코드베이스.
- 주요 의존성(`app/pubspec.yaml`): `http`(REST 통신), `shared_preferences`(로컬 영속화), `cupertino_icons`. Provider/Riverpod/Bloc 등 상태관리 패키지는 없고 `ChangeNotifier` + `setState`만 사용.
- 백엔드 접속 주소는 `AiApiClient.defaultBaseUrl`(`app/lib/services/ai_api_client.dart`)에서 결정: 빌드 시 `AI_API_BASE_URL` 환경변수 → 없으면 Android 에뮬레이터는 `http://10.0.2.2:8000`, 그 외는 `http://localhost:8000`.
- 애셋은 `assets/data/duty_2026_06.json` 하나뿐이며 2026년 6월 근무계획(94명분)을 앱 내장 리소스로 번들링.
- `main.dart`에서 `ConversationStore.init()`(로컬 대화 캐시 로드)와 `AuthSession.restore()`(로그인 세션 복원)를 수행한 뒤, 세션이 있으면 탭 셸(`AppShellWrapper`)로, 없으면 `LoginScreen`으로 분기.

### 1.2 화면별 기능 (실동작 vs Mock)

| 화면 | 파일 | 설명 | 상태 | 관련 API |
|---|---|---|---|---|
| 로그인 | `screens/login_screen.dart` | 사번/이메일+비밀번호 로그인 | **실동작** | `POST /auth/login` |
| 회원가입 | `screens/signup_screen.dart` | 이름/사번/노선(6호선 고정)/이메일/비밀번호, 클라이언트 유효성 검사 | **실동작** | `POST /auth/signup` |
| 홈 | `screens/home_screen.dart` | 인사말, 오늘의 근무 카드, 빠른 실행 그리드, 주간 근무 스트립, 채팅 입력바 | 내비게이션 허브(하위 위젯이 실데이터 사용) | — |
| 채팅 목록 | `screens/chat_list_screen.dart` | 저장된 대화 목록, 새 대화 시작 | **실동작**(로컬 저장) | — |
| 채팅방 | `screens/chat_room_screen.dart` | AI 질의응답, 응답모드(즉시/일반/심층) 선택, 근거 소스 카드, 대화 삭제 | **실동작** | `POST /ai/chat` |
| 규정 라이브러리 | `screens/regulation_library_screen.dart` | 규정 목록(카테고리별 그룹핑) | **실동작** | `GET /regulations` |
| 규정 원문 뷰어(목록발) | `regulation_library_screen.dart`(`RegulationDocumentScreen`) | 규정 본문 + 별표/별지 부속서류 이동 | **실동작** | `GET /regulations/document` |
| 규정 원문 뷰어(채팅발) | `screens/regulation_viewer_screen.dart` | 챗봇 답변 근거 조항 원문 표시, 북마크 토글 | **실동작** | `/bookmarks` |
| 보관함 | `screens/bookmark_screen.dart` | 저장한 규정 조항 목록, 삭제, 원문 이동 | **실동작** | `GET/POST/DELETE /bookmarks` |
| 시간표(근무표) | `screens/schedule_screen.dart` | 오늘/주간/타임라인 탭, 근무계획·교번표 진입 | **실동작**(로컬 JSON) | — |
| 근무표 업로드 | `screens/schedule_upload_screen.dart` | 파일 업로드 UI | **Mock** — 실제 파일 선택 없이 "샘플 파일 분석" 버튼으로 바로 완료 처리 | — |
| 근무·교번 보드 | `screens/duty_board_screen.dart` | 기관사별 월간 근무 달력, 일자별 교번표, 교번 상세시트 | **실동작**(파싱 데이터) — 단 교번 상세 시각·구간은 `turnDetailIsDummy` 플래그로 더미임을 UI에 명시 | — |
| 커뮤니티 목록 | `screens/community_list_screen.dart` | 자유/질문/비밀 게시판, FAQ·보관함 바로가기 | 내비게이션 허브(하드코딩 라벨) | — |
| 커뮤니티 게시판 | `screens/community_board_screen.dart` | 게시글 목록·상세 | **완전 Mock** — 하드코딩 게시글 3종, 글쓰기는 "준비 중" | — |
| FAQ | `screens/faq_screen.dart` | 자주 묻는 질문 아코디언 | **완전 Mock** — 5개 문항 하드코딩 | — |
| 알림 | `screens/notification_screen.dart` | 알림 리스트 | **완전 Mock** — 3개 항목 하드코딩, 탭하면 "준비 중" | — |
| 마이페이지 | `screens/my_page_screen.dart` | 프로필 카드, 메뉴(정보수정/비번변경/알림설정/공지/로그아웃 등) | 프로필 표시·로그아웃만 **실동작**, 나머지 메뉴는 **Mock**("준비 중") | — |
| 설정 | `screens/settings_screen.dart` | 노선/규정버전 표시, 다크모드 토글 | 다크모드 토글만 **실동작**(`ThemeController`), 나머지는 정적 표시 | — |

### 1.3 인증 흐름

- `AuthSession`(정적 싱글턴)이 로그인 상태(`accessToken`, `tokenType`, `user`)를 보관하고 `SharedPreferences`(`auth_session` 키)에 영속화, 앱 시작 시 복원.
- 로그인/회원가입 성공 → `AuthSession.signIn()` → 탭 셸 전환. 로그아웃 → 확인 다이얼로그 후 `AuthSession.signOut()` → 로그인 화면으로 리셋 네비게이션.
- 로그인 화면의 "비밀번호 찾기" 버튼은 인증 없이 바로 앱에 진입시키는 **MVP 우회 로직**으로 코드에 명시되어 있음.
- `GET /auth/me`(`fetchCurrentUser`), `GET /ai/models`(`fetchModels`), `fetchRetrievers()`는 클라이언트에 구현되어 있으나 현재 어떤 화면에서도 호출되지 않는 미사용 메서드.

### 1.4 AI 챗봇 연동 방식

- `AiApiClient.ask()`가 `POST {baseUrl}/ai/chat` 호출 (타임아웃 90초).
  - 요청: `{question, k, retriever?, model?, generation_mode?}`
  - 응답: `{answer, sources: [{score, title, file_name, content, linked_annex, source, chunk_id, retriever}], searchKeywords}`
- **리트리버 선택지**(`core/ai_retriever.dart`): `hybrid`(기본) / `local_graph` / `local_fts` / `local_vector` / `local_vector_openai` 5종이 정의되어 있으나, 앱은 항상 `hybrid`를 고정 사용 — 사용자가 UI에서 검색기를 바꾸는 화면은 없음.
- **응답 모드**(채팅방 상단 `SegmentedButton`): 즉시 응답(`fast_extractive_v1`, top-k 3) / 일반 채팅(`llm_relevancy_v2`, `gpt-4o-mini`, top-k 3, 기본) / 심층 응답(`llm_relevancy_v2`, `gpt-4o`, top-k 5).
- 첫 번째 근거(`sources.first`)만 근거 카드로 표시, 탭하면 규정 원문 뷰어로 이동해 전문·북마크 제공.
- 서버 미기동/타임아웃/에러 시 한국어 오류 메시지를 분기 처리하여 노출.

### 1.5 로컬 저장/캐싱

- **`ConversationStore`**: `SharedPreferences`(`conversations_v1`)에 대화 목록 저장. 최초 실행 시 저장 데이터가 없으면 `mock_conversations.dart`의 샘플 5개로 시드. 서버 동기화 없는 순수 로컬 저장.
- **`BookmarkStore`**: 서버(`/bookmarks`)를 진실 소스로 삼되 낙관적 업데이트 — 토글 즉시 로컬 갱신 후 백그라운드로 서버 반영(실패해도 로컬 유지, 오프라인 폴백).
- **`AuthSession`**: `SharedPreferences`(`auth_session`)에 세션 저장.
- **`DutyRepository`**: 앱 번들 자산(`assets/data/duty_2026_06.json`)을 1회 로드 후 메모리 캐시. 서버 API 없음.
- **`ThemeController`**: 다크모드 상태는 메모리에만 보관(영속화 없음, 재시작 시 라이트모드로 리셋).

### 1.6 공통 UI 컴포넌트 (`app/lib/widgets/`)

- 레이아웃: `app_card`, `app_page`, `page_header`, `section_header`, `board_header`, `campus_header`
- 근무/시간표 시각화: `today_duty_card`, `weekly_duty_strip`, `weekly_grid_view`, `train_flow_timeline`
- 채팅: `chat_bubble`, `chat_composer`, `chat_input_bar`
- AI 근거 표시: `evidence_source_card`, `evidence_mini_label`, `highlight_text`(인용문 하이라이트)
- 기타: `quick_action_grid`, `status_pill`, `recent_item`, `board_post`, `skeleton`(로딩 placeholder)

---

## 2. 백엔드 / AI (`back/`, `ai_legacy/`)

> `ai/`가 비어 있어 `ai_legacy/`를 실질적인 현재 구현으로 간주하여 분석.

### 2.1 개요

- **프레임워크**: FastAPI (`ai_legacy/api.py`의 `create_app()`)
- **진입점**: `back/main.py` — 루트를 `sys.path`에 등록, `ai/.env` 로드 후 `from ai.api import app`. 실행: `uvicorn back.main:app --reload`
- **의존성**(`back/requirements.txt`): `fastapi`, `uvicorn[standard]`, `python-dotenv`, `neo4j`, `langchain-core`, `langchain-openai`, `langchain-neo4j`, `pydantic`
- **CORS**: `CORS_ORIGINS` 환경변수(기본 `*`)
- **설정**(`ai_legacy/config.py`): `DATA_DIR`, `LOCAL_DB_DIR`, SQLite 경로, `OPENAI_API_KEY`, `EMBEDDING_MODEL`(기본 `text-embedding-3-small`), `LLM_MODEL`(기본 `gpt-4o-mini`), `AI_GENERATION_MODE`(기본 `llm_relevancy_v2`), `AI_RETRIEVER`(기본 `hybrid`)

### 2.2 API 엔드포인트 전체 목록

| 경로 | 메서드 | 기능 |
|---|---|---|
| `/health` | GET | 헬스체크 |
| `/ai/health` | GET | AI 서브시스템 상태(기본 검색기, 로컬 DB 존재 여부, OpenAI 키 설정 여부) |
| `/ai/models` | GET | 사용 가능한 LLM 모델 목록·기본값 |
| `/ai/retrievers` | GET | 사용 가능한 검색기 옵션·기본값·로컬 DB 상태 |
| `/auth/signup` | POST | 회원가입 |
| `/auth/login` | POST | 로그인(이메일 또는 사번) |
| `/auth/me` | GET | Bearer 토큰으로 현재 사용자 조회 |
| `/ai/index/local/rebuild` | POST | 로컬 SQLite 검색 인덱스 재구축 |
| `/ai/compare` | POST | 여러 검색기로 동일 질문을 병렬 비교 |
| `/ai`, `/ai/chat` | POST | RAG 질의응답(핵심 기능) — `question`, `retriever`, `model`, `generation_mode`, `k` |
| `/bookmarks` | GET/POST/DELETE | 규정 조항 보관함 CRUD |
| `/duties/meta` | GET | 근무표 메타(월, 노선, 날짜 목록, 기관사 목록) |
| `/duties` | GET | 특정 일자의 교번 배정 목록 |
| `/duties/driver/{no}` | GET | 특정 기관사의 월간 근무 캘린더 |
| `/regulations` | GET | 규정 원문 카탈로그 |
| `/regulations/document` | GET | 규정 본문 + 부속서류(경로 탈출 방지 검증 포함) |

모든 엔드포인트가 실제로 배선되어 동작하는 완성 코드로 보이며, 실험/미완성 흔적은 없다. 단 `schema.sql`에는 `quiz_questions`, `fault_guides`, `shift_swaps`, `standby_coverage`, `conversations`/`messages`, `board_posts`/`board_comments`, `faqs`, `safety_items`, `notices` 등 다수 테이블이 정의되어 있으나 **API로 노출되지 않은 선행 스캐폴딩**(향후 기능용)으로 남아 있다.

### 2.3 인증/사용자 관리 (`ai_legacy/auth_service.py`)

- 완성된 자체 인증: 회원가입, 로그인, 토큰 검증.
- 비밀번호는 PBKDF2-SHA256(26만 iteration) + salt 해싱, 세션 토큰은 SHA-256 해시로 저장(30일 만료).
- 별도 `auth.sqlite`에 `users`(이름/사번/이메일/노선/비밀번호해시), `sessions`(토큰해시/만료시각) 테이블.
- 유효성 검증: 이메일 형식, 비밀번호 8자 이상, 사번·이메일 유니크(중복 시 409).
- `init_db.py`에서 `role`, `office` 컬럼을 후행 마이그레이션으로 보강.

### 2.4 규정 검색(RAG) 파이프라인

기본 검색기는 `hybrid`. 모두 SQLite 로컬 인덱스(`local_index.py`가 빌드: `chunks`, `chunks_fts`(FTS5), `vectors`, `graph_nodes`/`graph_edges`) 위에서 동작.

- **`local_fts`**: SQLite FTS5(bm25) + LIKE 부분일치 + "제N조/별표N" 등 패턴 정확매치를 병합, 제목/본문 가중치 커스텀 스코어링.
- **`local_vector`**: 코사인 유사도 검색. 기본 임베딩은 외부 의존성 없는 **해시 기반 결정론적 벡터화**(의미 기반이 아닌 어휘 기반 베이스라인).
- **`local_vector_openai`**: OpenAI `text-embedding-3-small` 임베딩 기반 별도 벡터 DB, 존재할 때만 활성화.
- **`local_graph`**: FTS로 시드 청크를 찾은 뒤 그래프 엣지(`LINKS_TO`/`REFERENCES`)를 1-hop 확장.
- **`hybrid`**(기본): `local_graph` + `local_fts` + `local_graph_aux`(+옵션 벡터 검색기)를 병렬 실행 후 **RRF(Reciprocal Rank Fusion) + 도메인 어휘 부스팅**(관제/승무/폐색/음주 등 가중치 규칙)으로 재정렬.
- **답변 생성**: OpenAI 미설정 시 컨텍스트 스니펫 발췌 조립(추출적 답변)으로 폴백. 설정 시 `langchain-openai`의 `ChatOpenAI`로 생성. 생성 모드가 5종 이상 프롬프트 프리셋(`llm_context_only_v1`, `llm_relevancy_v2~v4`, `llm_balanced_v1`, `fast_extractive`)으로 구현되어 프롬프트 A/B 실험 흔적이 뚜렷함.

### 2.5 지식 그래프 기능 (Neo4j) — 사용되지 않는 레거시 실험

- `create_graph.py`: 청크를 OpenAI 임베딩 후 Neo4j에 `DocFile`/`Article`/`Annex`/`Concept` 노드와 관계, 벡터 인덱스를 구축하는 일회성 오프라인 스크립트.
- `retrievers/neo4j_vector.py`: Neo4j 벡터 인덱스 검색 리트리버 구현.
- 그러나 `config.py`에는 더 이상 `NEO4J_*` 상수가 정의되어 있지 않고, `retrievers/factory.py`도 이 모듈을 import하지 않아 **`get_retriever()`로 절대 선택될 수 없는 orphan 코드**. `hybrid`의 `INCLUDE_NEO4J_IN_HYBRID` 옵션도 실제로는 어디서도 사용되지 않음.
- 결론: Neo4j 기반 그래프 RAG는 SQLite 기반 로컬 그래프(`local_graph`)로 대체된 사용되지 않는 실험으로 판단.

### 2.6 데이터 전처리 도구 (`tools/`)

- **`hwp_md_tables.py`**: `.hwp` 원본을 ODT로 변환해 표(셀 병합 포함) 구조를 추출, 변환된 규정 MD의 flatten된 표를 원본 구조 그대로의 HTML `<table>`로 치환.
- **`link_annexes.py`**: 규정 본문에서 "[별표 N]"/"[별지 N호]" 패턴을 찾아 옵시디언 위키링크로 자동 연결(+역링크) — RAG 그래프 인덱싱(`LINKS_TO`/`REFERENCES`)의 전제 조건.
- **`parse_duty_xlsx.py`**: 근무계획 엑셀을 파싱해 기관사별 일자 근무 코드를 분류하고 `app/assets/data/duty_2026_06.json`으로 변환. 교번(turn)별 다이아 상세(출발/도착역, 열차번호)는 원본에 없어 **결정론적 더미 데이터로 생성**한다고 코드 주석에 명시.
- **`pptx_to_obsidian.py`**: "6호선 전동차고장조치 길라잡이" PPTX를 시나리오별로 분해해 옵시디언 MD로 변환, 슬라이드 이미지 추출, 시나리오→관련 규정 조항 매핑(PDF OCR 기반 44장)으로 위키링크 연결.

### 2.7 데이터 자산 (`data/`)

RAG 파이프라인의 소스 코퍼스:

- `data/규정/`: 관제업무·복무보수·안전관리·예규·운전관리규정·인사교육 등 카테고리별 규정 원문(본문 + 별표/별지 부속서류 md), `_conversion_log.json`으로 변환 이력 추적.
- `data/규정_hwp/`: 규정 원본 HWP(표 복원용 소스).
- `data/길라잡이_pptx/`, `길라잡이_md/`, `길라잡이_pdf_with links/`: "6호선 전동차고장조치 길라잡이" 매뉴얼(원본 PPTX 2개, 시나리오별 옵시디언 MD, OCR 대조용 PDF 이미지).
- `data/2026년 6월 기관사 근무계획.xlsx`: 근무표 원본(`docs/`에도 동일 파일 존재).
- `data/.obsidian/`: 옵시디언 vault 설정 — 데이터가 위키링크 그래프 형태로 관리·편집됨을 의미.

즉 `data/`는 규정 원문과 고장조치 매뉴얼을 RAG 검색 가능한 마크다운/그래프 구조로 정제한 지식베이스이며, `tools/`가 원본(HWP/PPTX/XLSX)에서 이 구조로의 변환을 담당한다.

### 2.8 평가/실험 도구

- **`compare_retrievers.py`**: CLI(`python -m ai_legacy.compare_retrievers`) 및 `/ai/compare` API로 제공. 동일 질문을 여러 검색기에 병렬로 태워 응답시간·답변·근거를 비교, JSON/Markdown 리포트 출력. 기본 질문 5개(구원운전, ATC 고장, PSD 닫힘불능, 전령법, SIV 고장)가 하드코딩되어 반복 평가에 사용.
- **`ragas_testset.json`**: `question`/`reference`/`reference_context` 형식의 QA 평가셋(예: "TC1 고장 시 ATC/ATO 제한은?"). RAGAS 프레임워크 호환 형식으로 정량 평가용으로 추정되나, 이를 소비하는 실행 스크립트는 `ai_legacy/` 내에 없음(테스트셋만 존재, 평가 러너는 미포함/삭제됨).

---

## 3. 종합 정리

### 3.1 완성되어 실제로 동작하는 핵심 기능

- 회원가입/로그인/세션 관리 (자체 인증, PBKDF2 해싱)
- RAG 기반 규정 챗봇 (`/ai/chat`) — 5종 검색기, hybrid 기본, 다수 생성 모드 프리셋
- 규정 원문 라이브러리·뷰어 (부속서류 연결 포함)
- 규정 조항 북마크(보관함) — 서버 동기화 + 로컬 낙관적 업데이트
- 근무표/교번 조회 API 및 화면 (단, 다이아 상세는 더미 데이터)
- 검색기 비교 도구(`/ai/compare`, CLI)

### 3.2 Mock/미완성 상태로 남아있는 기능

- 커뮤니티 게시판, FAQ, 알림 화면 — 전부 하드코딩된 정적 데이터
- 근무표 업로드 — 실제 업로드 로직 없이 버튼 하나로 완료 처리
- 마이페이지의 정보수정/비번변경/알림설정 등 메뉴 — "준비 중" 처리
- DB 스키마상 존재하나 API로 노출되지 않은 테이블(퀴즈, 고장조치 가이드, 교대 신청, 대기 배정, 대화 이력, 게시판, FAQ, 안전 항목, 공지 등) — 향후 기능을 위한 선행 스캐폴딩

### 3.3 사용되지 않는/버려진 코드

- `ai_legacy/retrievers/neo4j_vector.py`, `create_graph.py`, `query_graph.py` — Neo4j 기반 그래프 RAG. `config.py`에서 관련 설정이 이미 제거되어 factory에서 선택 불가능한 orphan 코드.
- `ragas_testset.json` — 평가셋만 있고 실행 러너 없음.

### 3.4 이관 시 유의점

- `ai/` 디렉토리가 비어 있어 `back/main.py`의 `from ai.api import app` 경로가 현재 깨져 있음. 신규 레포에서 백엔드를 살리려면 `ai_legacy/`의 구조를 참고해 재구성이 필요.
- Flutter 앱은 `hybrid` 검색기를 하드코딩해 사용 중이며, 검색기/모델 선택 UI는 만들어졌지만(`fetchRetrievers`, `fetchModels`) 실제로 연결되어 있지 않음.
- 루트 `README.md`는 `llm_test/`(검색/평가 실험 코드) 디렉토리를 언급하지만 현재 워킹트리와 git 이력 전체에 해당 디렉토리는 존재하지 않음(생성된 적 없음) — README 기술이 실제 구조와 어긋난 부분이므로 신규 문서 작성 시 그대로 옮기지 않도록 주의.

### 3.5 테스트 커버리지

- `app/test/widget_test.dart`에 Flutter 위젯 테스트 3건 존재: ① 홈 화면 진입("오늘의 승무 지원" 등 표시) ② 근무표 탭 이동 → 업로드 화면 → "샘플 파일 분석" 실행 → 열차 흐름/교번 상세 표시까지의 흐름 ③ 채팅 탭 이동 → 대화 목록에서 항목 선택 → 채팅방 진입 및 "근거 확인됨" 라벨 표시. 백엔드(`ai_legacy/`) 쪽에는 별도 자동화 테스트 코드가 없음.

### 3.6 조사 범위에서 제외한 것

- `.codegraph/`(빈 디렉토리), `.omo/run-continuation/`(AI 코딩 에이전트 세션 로그), `.claude/`(Claude Code 설정) — 앱이 제공하는 기능이 아닌 개발 툴링/세션 아티팩트이므로 기능 목록에서 제외.
- `docs/`의 발표자료(PPT/HTML 프레젠테이션)는 로드맵·기획 문서 성격이라, 실제 구현된 기능만 다루는 이 보고서의 범위에서는 참고자료로만 언급하고 세부 내용은 다루지 않음.
