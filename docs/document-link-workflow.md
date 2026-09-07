# 구절·페이지 기반 문서 연결

2026-09-07 구현 기준. 이전 `link-generator-system-overview.md`의 fragment 기반 UI를 대체한다.

## 사용자 동작

- DOCX·HWP·HWPX: 읽기 전용 평문에서 드래그 → **구절 추가**. 문단을 가로질러도 하나의 구절이며, 한쪽에 여러 구절을 더할 수 있다. 겹치는 구절은 새 선택으로 대체된다. 본문 찾기, Shift+방향키, Ctrl+A, Ctrl+Home/End를 지원한다.
- PDF: 원본 페이지를 보며 **이 페이지 선택** 또는 썸네일 체크박스를 사용한다.
- PPTX: 원본 슬라이드를 보며 **이 슬라이드 선택** 또는 썸네일 체크박스를 사용한다. 기본 화면에는 PDF 변환기가 필요하지 않다.
- 비연속 구절·페이지도 한 묶음으로 선택할 수 있다. 구절 n개 ↔ 페이지 m개가 링크 하나다. 이동·반대편 조작 후에도 선택이 유지되며 하단에서 개별 해제한다.
- 하단에서 양쪽 인용문·썸네일과 메모를 확인하고 저장한다. 저장 한 번은 링크 하나다.
- **연결 검토**에서 선택 확인·수정, 승인, 반려한다. 승인된 연결을 수정하면 초안으로 돌아간다.
- **검색 검증**에서 답변과 연결된 원문을 확인한다. 텍스트 없는 페이지는 원본 확인 대상으로 표시하며, 그림 내용을 AI가 읽었다고 주장하지 않는다.

문서 탐색은 양쪽 문서를 열면 접힌다. 다시 펼쳐 문서를 바꿀 수 있다. 원본 확인은 해당 버전의 원본 파일을 연다. 브라우저가 직접 표시할 수 없는 형식은 다운로드될 수 있다.

## 데이터와 API

`document_contents`는 문서 버전별 불변 평문 또는 전체 페이지 목록을 보존한다. 텍스트가 없는 PDF 페이지도 포함한다. 새 ingestion은 원본을 `runtime/storage/originals/<version_id>/`에 복사한다.

`document_links`는 fragment ID 없이 양쪽 선택, 관계, 메모, 승인·감사 정보를 저장한다.

```json
{
  "source_selection": {
    "kind": "text", "version_id": "문서-A-버전-ID",
    "ranges": [{"start": 0, "end": 3, "exact": "ATC"}]
  },
  "target_selection": {
    "kind": "pages", "version_id": "문서-B-버전-ID", "pages": [1, 3]
  },
  "relation_type": "RELATED", "note": "관련 조치 자료"
}
```

- `ranges`는 시작 위치 순으로 정렬해 저장하며 서로 겹치면 거부한다. 이전에 저장된 단일 구절(`start`·`end`·`exact`가 최상위에 있는 형태)도 그대로 읽는다.
- 텍스트 위치는 표시된 평문의 UTF-16 코드 단위이며 끝 위치는 제외한다. 서버는 정확한 인용문을 대조하고 앞뒤 문맥을 기록한다. 이모지 중간을 자르는 범위는 거부한다.
- 페이지 번호는 1부터 시작하며 PPTX에서는 슬라이드 번호다. 서버가 정렬·중복 제거하고 존재 여부를 검증한다.
- `GET /api/documents/{id}/content?version_id=...`: 전체 평문 또는 페이지 번호 목록.
- `GET /api/documents/{id}/source?version_id=...`: 해시를 확인한 해당 버전의 원본. PDF 변환 API도 같은 버전 인자를 지원한다.
- `POST /api/links`, `GET /api/links[?status=draft|approved|rejected]`, `GET/PUT /api/links/{id}`.
- `POST /api/links/{id}/approve`, `/reject`: 기존과 같은 `{ "actor": "local-admin" }` 요청.
- `/api/rag/query`: 응답에 `link_id`, `selection`, `document_id`, `filename`, `text` 근거 필드를 추가한다. 기존 검색 근거는 `fragment`를 유지한다. 새 구절·페이지 근거는 `fragment=null`이며 `text`와 `selection`을 사용한다. 실재하지 않는 fragment ID를 외부에 노출하지 않으며, 외부 RAG 클라이언트는 이 분기를 처리해야 한다.

임베딩은 별도 검색 인덱스다. 텍스트 청크에는 전체 평문에서의 범위를, 페이지 청크에는 페이지 번호를 기록한다. 승인 링크를 따라 선택 범위 단위로 검색을 확장하며 청크 쌍의 모든 조합을 링크로 저장하지 않는다. 인덱스를 다시 만들어도 문서 본문과 링크를 변경하지 않는다.

## 기존 데이터와 제한

- SQLite와 PostgreSQL 모두 시작 시 새 테이블만 생성한다. DB 관리자가 사전 적용할 경우 `back/migrations/003_document_links.sql`을 사용한다. 이전 마이그레이션도 필요한 기존 DB에는 먼저 적용한다.
- 기존 `knowledge_edges` 및 API는 유지한다. 화면에서는 **이전 방식 연결**로 별도 표시하고 승인·반려할 수 있다. 자동으로 합치거나 새 구절 링크로 추정 변환하지 않는다.
- 기존 문서를 열 때 원본 해시를 검사하고 빠진 선택용 본문과 평문 인덱스를 추가한다. 기존 fragment와 edge는 삭제하지 않는다. 반복 문장의 위치가 불명확한 이전 fragment는 새 구절과 임의로 대응시키지 않는다.
- 보존된 원본이 없거나 해시가 다르면 재선택·저장을 막고 오류를 표시한다. 새 버전으로 연결을 자동 이전하지 않는다.
- DOCX는 본문 문단·표를 문서 순서대로 읽으며 표 셀은 탭, 행은 줄바꿈으로 표현한다. 본문 밖 머리글·바닥글, 도형 안 텍스트, 원본 페이지 레이아웃 재현은 지원 범위 밖이다.
- OCR, 이미지 내부 영역 선택, 페이지 문서에서의 세밀한 텍스트 링크는 이번 버전에 포함하지 않는다.
- 인증은 기존 개발용 관리자 표시 수준이다. 문서 처리와 첫 기존 문서 인덱스 보충은 동기적으로 실행된다.

## 검증

```powershell
cd back
uv sync --extra hwp --extra dev
uv run pytest
uv run ruff check app tests
cd ../front/link-generator
npm.cmd run build
```

격리된 브라우저 검증은 별도 터미널에서 다음 두 명령을 실행한다. 사용자 DB 대신 새 임시 폴더의 문서·DB와 로컬 해시 임베딩을 사용한다.

```powershell
uv --directory back run --extra dev python tests/serve_link_qa.py
uv --directory back run --extra dev python tests/serve_link_qa.py --ui
```

`http://127.0.0.1:15173`에서 직접 확인하거나, Playwright가 설치된 환경에서 `node front/link-generator/tests/link-workflow.cjs`를 실행한다. Playwright가 다른 경로에 있으면 `PLAYWRIGHT_PACKAGE`에 패키지 절대 경로를 지정한다. 스크린샷은 `back/runtime/link-qa/`에 저장된다. 검증 후 두 테스트 서버를 종료한다.
