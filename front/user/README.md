# Da-Al-G 사용자 앱

백엔드의 `POST /api/chat`을 호출하는 일반 대화·문서 RAG 채팅 앱입니다.

앱을 열면 로그인 화면이 표시됩니다. 개발 서버가 `ENABLE_TEST_ACCOUNT=true`이면 `test/test`로 로그인할 수 있습니다. 앱 회원가입은 없으며 계정은 관리자가 발급합니다. 채팅 기록과 북마크는 로그인 시 서버에 동기화되고, 근무표는 관리자가 업로드한 월별 데이터에서 읽습니다.

```powershell
cd front/user
flutter pub get
flutter run
```

웹 빌드는 접속한 서버의 API를 사용하고, 모바일 빌드의 기본 API 주소는 `https://2026-da-al-g-production.up.railway.app`입니다. 개발 환경에서 다른 서버를 사용하려면 다음처럼 실행합니다.

```powershell
flutter run --dart-define=API_BASE_URL=http://localhost:8000
```

Railway API를 사용하는 APK는 다음처럼 빌드합니다.

```powershell
flutter build apk --release
```

로컬 백엔드 개발이 필요할 때만 백엔드를 실행합니다.

```powershell
cd back
uv run uvicorn app.main:app --reload --port 8000
```
