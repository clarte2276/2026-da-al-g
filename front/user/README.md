# Da-Al-G 사용자 앱

백엔드의 `POST /api/chat`을 호출하는 일반 대화·문서 RAG 채팅 앱입니다.

앱을 열면 로그인 화면이 표시됩니다. 개발 서버가 `ENABLE_TEST_ACCOUNT=true`이면 `test/test`로 로그인할 수 있고, 회원가입으로 일반 계정을 만들 수도 있습니다. 앱을 다시 실행하면 세션 보호를 위해 다시 로그인합니다.

```powershell
cd front/user
flutter pub get
flutter run
```

기본 API 주소는 모든 플랫폼에서 `https://2026-da-al-g-production.up.railway.app`입니다. 개발 환경에서만 다른 서버를 사용하려면 다음처럼 실행합니다.

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
