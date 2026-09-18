# Da-Al-G 사용자 앱

백엔드의 `POST /api/chat`을 호출하는 일반 대화·문서 RAG 채팅 앱입니다.

앱을 열면 로그인 화면이 표시됩니다. 개발 서버가 `ENABLE_TEST_ACCOUNT=true`이면 `test/test`로 로그인할 수 있고, 회원가입으로 일반 계정을 만들 수도 있습니다. 앱을 다시 실행하면 세션 보호를 위해 다시 로그인합니다.

```powershell
cd front/user
flutter pub get
flutter run
```

기본 API 주소는 웹·Windows·macOS에서 `http://localhost:8000`, Android 에뮬레이터에서 `http://10.0.2.2:8000`입니다. 다른 주소를 사용하려면 다음처럼 실행합니다.

```powershell
flutter run --dart-define=API_BASE_URL=http://192.168.0.10:8000
```

Railway에 배포한 뒤에는 다음처럼 빌드합니다.

```powershell
flutter build apk --release --dart-define=API_BASE_URL=https://<railway-domain>
```

먼저 백엔드를 실행해야 합니다.

```powershell
cd back
uv run uvicorn app.main:app --reload --port 8000
```
