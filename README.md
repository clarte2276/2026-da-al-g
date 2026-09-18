# 6호선 길라잡이 Da-Al-G

철도 업무 문서에서 사람이 선택한 **구절 또는 페이지 묶음**을 연결하고, 승인된 관계를 Graph RAG 검색에 활용하는 초기 구현입니다.

- `back/`: FastAPI 문서 파싱·검색·연결 API
- `front/link-generator/`: React/Vite 문서 연결·검토·검색 화면
- `front/user/`: 일반 대화와 문서 RAG를 함께 지원하는 Flutter 채팅 앱
- `data_raw/`: 원천 업무 문서
- [현재 문서 선택 방식·API·데이터 전환·검증 안내](docs/document-link-workflow.md)
- [Railway 배포·인증·데이터 이전 안내](docs/railway-deployment.md)

## 연결 방식

| 문서 | 화면과 선택 |
| --- | --- |
| DOCX / HWP / HWPX | 완전한 읽기 전용 평문에서 원하는 구절 드래그 → 구절 지정 |
| PDF | 원본 페이지 표시 → 페이지 선택 |
| PPTX | 원본 슬라이드 표시 → 슬라이드 선택 |

페이지는 여러 장을 한 묶음으로 선택할 수 있습니다. 구절↔구절, 구절↔페이지, 페이지↔페이지 모두 **저장 한 번에 연결 하나**가 생성됩니다. 승인 후에만 그래프 검색에 반영되고, 승인된 연결을 수정하면 초안으로 돌아갑니다.

임베딩 청크는 내부 검색용입니다. 화면과 링크 저장은 문서 버전별 평문 위치 또는 페이지 번호를 기준으로 하며, 청크 수에 따라 사용자 링크가 나뉘지 않습니다.

## 실행

백엔드 (Python 3.11 이상):

```powershell
cd back
uv sync --extra hwp --extra dev
# 처음 설정할 때만 실행하고 LOCAL_DOCUMENT_ROOTS를 실제 문서 폴더로 수정
Copy-Item .env.example .env
uv run uvicorn app.main:app --reload --port 8000
```

프론트엔드 (별도 터미널):

```powershell
cd front/link-generator
npm.cmd install
npm.cmd run dev
```

백엔드 주소가 다르면 `front/link-generator/.env`의 `VITE_API_BASE_URL`을 설정합니다. 파일 탐색기는 백엔드 PC의 `LOCAL_DOCUMENT_ROOTS`를 탐색합니다.

사용자 채팅 앱:

```powershell
cd front/user
flutter pub get
flutter run
```

채팅 앱은 `POST /api/chat`을 사용하며, 일반 대화는 문서 검색 없이 답하고 문서 질문만 기존 Graph RAG로 처리합니다. API 주소는 `--dart-define=API_BASE_URL=http://호스트:8000`으로 바꿀 수 있습니다.

OpenAI 키가 없으면 로컬 해시 임베딩과 근거 발췌로 동작합니다. 키를 설정하면 OpenAI 임베딩과 답변 생성을 사용합니다. PDF/PPTX 페이지 선택은 텍스트 추출 여부와 무관하게 가능하지만 OCR·이미지 내용 분석은 포함하지 않습니다.

사용자 앱은 일반 로그인·회원가입을 지원하며 개발 테스트 계정은 `test/test`입니다. Railway 배포 시 백엔드의 HTTPS 주소를 `API_BASE_URL`로 넣어 앱을 빌드합니다. 자세한 배포 절차는 [Railway 배포 안내](docs/railway-deployment.md)를 참고하세요.

## 데이터

기본 DB는 SQLite이며 PostgreSQL + pgvector도 지원합니다. 새 연결용 테이블은 API 시작 시 추가 생성합니다. 기존 DB와 fragment 기반 링크는 보존하며 화면에서 이전 방식 연결로 구분합니다. 새 ingestion은 버전별 원본 복사본도 보존합니다.

기존 PostgreSQL DB의 사전 마이그레이션 파일은 `back/migrations/`에 있습니다. 새 구절·페이지 연결용 파일은 `003_document_links.sql`입니다.

## 검증

```powershell
cd back
uv run --extra hwp --extra dev pytest
uv run --extra dev ruff check app tests
cd ../front/link-generator
npm.cmd run build
```

[격리된 브라우저 검증 방법](docs/document-link-workflow.md#검증)을 통해 테스트용 DOCX·PDF·PPTX와 저장소의 HWP/HWPX 샘플로 선택·저장·승인·검색을 확인할 수 있습니다.

인증·권한은 개발용 관리자 표시 수준이며 문서 처리는 동기식입니다. DOCX 본문 밖 요소, OCR, 이미지 영역 선택, 문서 버전 사이의 자동 링크 이전은 현재 지원하지 않습니다.
