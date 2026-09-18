# daalgi-knowledge-api

FastAPI 기반 문서 ingestion 및 Graph RAG API입니다. 상세 실행 방법은 [프로젝트 README](../README.md)를 참고하세요.

주요 API:

- 현재 문서 선택·링크 API와 실행·전환 안내: [구절·페이지 기반 문서 연결](../docs/document-link-workflow.md)
- `GET /api/documents/{id}/content`: 버전별 전체 평문 또는 페이지 목록
- `POST /api/links`: 구절·페이지 묶음 사이의 연결 하나 생성
- `GET/PUT /api/links/{id}`: 선택 확인·수정 (수정 시 초안 복귀)
- `POST /api/links/{id}/approve`, `/reject`: 연결 승인·반려

- `GET /api/local/roots`: 설정된 로컬 문서 폴더 조회
- `GET /api/local/files`: 로컬 `.hwp`, `.hwpx`, `.pptx`, `.pdf` 파일 탐색
- `POST /api/local/open`: 파일을 파싱·인덱싱하고 viewer용 document/version 반환
- `GET /api/documents/{document_id}/source`: 브라우저 원본 렌더러용 원본 바이트 스트리밍
- `POST /api/documents/upload`: `.hwp`, `.hwpx`, `.pptx`, `.pdf` 업로드 및 동기 ingestion
- `GET /api/documents/{document_id}/fragments`: 문서 fragment 조회
- `POST /api/edges`: 선택 영역 `source_anchor`/`target_anchor`를 포함한 단일 edge 초안 생성 (`relation_type` 기본값 `RELATED`)
- `POST /api/edges/batch`: 양쪽의 여러 anchor 조합으로 다대다 edge 초안 생성
- `GET /api/edges?status=draft`: 승인 대기 edge 조회
- `POST /api/edges/{edge_id}/approve`: edge 승인
- `GET /api/fragments/{fragment_id}/neighbors`: 승인된 이웃 조회
- `POST /api/rag/query`: vector seed + approved graph expansion 질의
- `POST /api/chat`: 일반 대화와 문서 질문을 자동 분기하는 하이브리드 채팅
- `GET /api/documents/{document_id}/page.png`: 근거가 나온 원본 페이지를 PNG로 렌더 (`page` 또는 `quote` 중 하나 지정, 변환 중이면 `202`)

원본 페이지 렌더링:

- PPTX·DOCX·HWP는 LibreOffice로 PDF를 만든 뒤 PyMuPDF로 한 쪽을 PNG로 굽고 `STORAGE_ROOT`에 캐시합니다.
- HWP는 LibreOffice 확장 [H2Orestart](https://github.com/ebandal/H2Orestart)가 있어야 제대로 변환됩니다. 없으면 pyhwp(`uv sync --extra hwp`)로 우회하지만 큰 문서는 수십 분이 걸립니다. 확장은 `STORAGE_ROOT/libreoffice-profile` 프로필에 설치합니다.

```powershell
& "C:\Program Files\LibreOffice\program\unopkg.exe" add -f "-env:UserInstallation=file:///<STORAGE_ROOT>/libreoffice-profile" H2Orestart.oxt
```

- 첫 변환은 문서 크기에 따라 수십 초가 걸립니다. ingestion 후 미리 변환해 두려면 `uv run python -m scripts.prewarm_pages`를 실행합니다.

인증:

- `POST /api/auth/register`, `POST /api/auth/login`: 일반 회원가입·로그인
- `GET /api/auth/me`, `POST /api/auth/logout`: 현재 세션 확인·폐기
- 로그인 토큰은 Argon2 비밀번호 해시와 DB 세션으로 관리하며, 문서 관리 API는 관리자 역할을 요구합니다.
- `ENABLE_TEST_ACCOUNT=true`일 때 `test/test` 계정이 시작 시 생성됩니다.
