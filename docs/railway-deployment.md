# Railway 배포

이 프로젝트는 Railway에서 FastAPI API와 관리자 React 화면을 하나의 서비스로 실행합니다. Dockerfile이 `back/`의 Python 앱과 `front/link-generator/`의 React 빌드를 함께 만들고, 배포된 API 주소의 `/admin/`에서 문서 연결 도구를 제공합니다.

## Railway 프로젝트 만들기

1. 저장소를 GitHub에 push합니다.
2. Railway에서 `New Project` → `Deploy from GitHub Repo`로 저장소를 선택합니다.
3. 저장소 루트의 `Dockerfile`과 `railway.json`을 그대로 사용합니다.
4. 서비스의 Settings → Networking → Public Networking에서 `Generate Domain`을 선택합니다.
5. 발급된 `https://....railway.app` 주소를 기록합니다. 이 주소가 API 주소이며 `/admin/`을 붙이면 관리자 화면입니다.

Railway는 서비스가 `$PORT` 환경변수를 주입하므로 Dockerfile은 해당 포트에서 `0.0.0.0`으로 Uvicorn을 실행합니다. `/health`가 배포 상태 확인 경로입니다.

## Volume과 환경변수

서비스에 Volume을 하나 추가하고 Mount Path를 `/data`로 지정합니다. SQLite DB, 업로드 원본, 변환 결과가 모두 이 경로에 저장되어야 재배포 후에도 유지됩니다.

Variables에 다음 값을 추가합니다.

```dotenv
DATABASE_URL=sqlite:////data/daalgi.db
STORAGE_ROOT=/data/storage
LOCAL_DOCUMENT_ROOTS=/data/documents
EMBEDDING_PROVIDER=auto
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
OPENAI_API_KEY=실제_OpenAI_키
LLM_MODEL=gpt-4o-mini
ENABLE_REGISTRATION=true
ENABLE_TEST_ACCOUNT=true
AUTH_SESSION_HOURS=24
CORS_ORIGINS=*
```

관리자 계정을 처음 만들 때만 아래 두 변수를 추가합니다. 첫 배포 후 관리자 로그인을 확인하면 `BOOTSTRAP_ADMIN_PASSWORD`는 삭제하는 편이 좋습니다. 이미 같은 아이디가 있으면 서버가 비밀번호를 덮어쓰지 않습니다.

```dotenv
BOOTSTRAP_ADMIN_USERNAME=admin
BOOTSTRAP_ADMIN_PASSWORD=긴_관리자_비밀번호
BOOTSTRAP_ADMIN_DISPLAY_NAME=문서 관리자
```

`ENABLE_TEST_ACCOUNT=true`이면 일반 사용자 테스트 계정 `test/test`가 서버 시작 시 없을 때 생성됩니다. 실제 외부 공개 전에는 테스트 계정을 끄고 다시 배포합니다.

Railway의 Volume은 기본 용량이 요금제별로 다릅니다. 현재 문서 기준 Free/Trial은 0.5GB, Hobby는 5GB입니다. Volume에는 서비스 복제 제한과 재배포 시 짧은 중단이 있으므로 이 구성은 단일 서비스 운영을 전제로 합니다. [Railway Volume 문서](https://docs.railway.com/volumes/reference)

## 원문 페이지 렌더링 의존성

채팅 근거의 "원문 페이지 보기"는 원본을 PDF로 변환한 뒤 한 쪽을 PNG로 렌더합니다. Dockerfile이 이미 필요한 것들을 설치합니다.

- `libreoffice`: PPTX·DOCX·ODT → PDF 변환기
- `fonts-noto-cjk`: 변환 결과의 한글 글꼴
- `H2Orestart` LibreOffice 확장: HWP는 LibreOffice 자체 필터가 글자를 깨뜨립니다. 이 확장이 있으면 4MB 규정 문서도 1분 안에 변환됩니다
- `uv sync --extra hwp`: 확장이 없을 때만 쓰는 pyhwp(`hwp5odt`) 폴백입니다. 큰 문서는 수십 분이 걸리므로 확장 설치가 사실상 필수입니다
- `pymupdf`: PDF 쪽을 PNG로 래스터화

첫 조회 때 변환이 시작되고, 끝나기 전에는 API가 `202`를 돌려주며 앱이 자동으로 다시 시도합니다. 배포 후 미리 변환해 두려면 서비스 셸에서 `python -m scripts.prewarm_pages`를 실행합니다.

변환한 PDF와 페이지 PNG는 `STORAGE_ROOT` 아래 `converted-pdf/`, `page-images/`에 캐시되므로 Volume(`/data/storage`)을 그대로 쓰면 재배포 후에도 유지됩니다. 첫 요청은 LibreOffice 변환 때문에 수 초에서 수십 초가 걸릴 수 있습니다.

## 첫 배포 후 확인

브라우저에서 다음 주소를 확인합니다.

```text
https://<railway-domain>/health
https://<railway-domain>/docs
https://<railway-domain>/admin/
```

`/admin/`에서는 관리자 계정으로 로그인합니다. 일반 사용자는 Flutter 앱에서 `test/test`로 로그인하고, 회원가입한 계정도 사용할 수 있습니다. 일반 사용자가 관리자 API를 호출하면 `403`이 반환되어야 합니다.

## Flutter 빌드

Railway 도메인을 API 주소로 넣어 Android APK를 만듭니다.

```powershell
cd front/user
flutter pub get
flutter build apk --release --dart-define=API_BASE_URL=https://<railway-domain>
```

APK는 `front/user/build/app/outputs/flutter-apk/app-release.apk`입니다. Flutter Web으로 배포하려면 다음 명령으로 `build/web`을 만들고 정적 호스팅에 올립니다.

```powershell
flutter build web --release --dart-define=API_BASE_URL=https://<railway-domain>
```

Flutter Web을 별도 도메인에 올릴 때는 그 도메인을 `CORS_ORIGINS`에 쉼표로 추가합니다. Android·iOS 설치형 앱은 브라우저 CORS의 영향을 받지 않습니다.

## 기존 데이터 이전

기존 로컬 문서를 사용하려면 문서 원본과 SQLite DB를 함께 이전해야 합니다. Railway Volume의 `/data/documents`에 문서를 복사하고, 기존 DB 파일을 `/data/daalgi.db`로 복사한 뒤 서버를 재시작합니다. DB에 기록된 `D:\...` 경로가 남아 있다면 `Document.source_path`와 `DocumentVersion.storage_path`를 `/data/...` 경로로 변경해야 합니다.

이전 후 다음을 확인합니다.

- 문서 수·버전 수·연결 수가 로컬과 같습니다.
- 관리자 화면에서 문서 원본과 연결 검토가 열립니다.
- `test/test` 로그인 후 채팅과 검색 근거가 동작하고, 근거 카드의 "원문 페이지 보기"가 원본 페이지를 보여줍니다.
- 서비스를 재배포한 뒤에도 계정·문서·연결이 남아 있습니다.

## 백업과 운영 주의사항

Railway Volume 백업에서 일일 또는 주간 일정을 설정합니다. 백업은 복구 수단이지 별도 외부 백업을 대신하지 않으므로 중요한 데이터는 DB와 `/data/storage`를 주기적으로 다른 저장소에도 보관합니다. [Railway 백업 문서](https://docs.railway.com/volumes/backups)

문서 업로드·변환은 요청 안에서 동기 처리됩니다. Railway의 공개 네트워크는 업로드 완료와 응답에 제한이 있으므로 큰 파일이나 여러 사용자의 동시 업로드가 필요해지면 ingestion 작업을 별도 worker로 분리합니다.
