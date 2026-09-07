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
