# dia5.kr 기능/API 크롤링 보고서

## 0. 조사 개요

- 대상: https://dia5.kr/
- 조사 시각: 2026-08-18 (KST)
- 확인된 빌드: v3.8.1
- 조사 방식:
  - Orca 내장 브라우저에서 홈, 근무, 안전, 교육, 라이프, 대기충당확인과 하위 화면을 순회했다.
  - 브라우저 네트워크 기록으로 실제 로딩 요청과 응답의 상위 구조를 확인했다.
  - Next.js 정적 청크에서 fetch 호출, Supabase 테이블, localStorage 키, 정적 JSON·이미지 경로를 교차 확인했다.
- 로그인된 운전직 세션을 사용했지만 이름·사번·사용자 ID·토큰·익명 ID·전화번호·실제 레코드 ID는 기록하지 않았다.
- 등록·삭제·로그인 변경·PIN 변경 등 상태를 바꾸는 요청은 제출하지 않았다. 변경 API는 화면 코드에서 확인한 요청 계약만 정리했다.

이 사이트는 기관사 업무 도구와 생활 편의 기능을 합친 Next.js/PWA 내부 포털이다. 데이터 원천은 다음 네 종류로 분류된다.

1. 사이트 서버의 /api/* 라우트: 인증, 뉴스, 실시간 열차, 안전, 교육, 피드백 등.
2. Supabase REST/Realtime/Storage: 근무 교체, 알림, 이미지 파일 등.
3. 번들 정적 데이터와 브라우저 저장소: 근무표, 교번, 일정·메모, 교육 교재, 게임·힐링카드 등.
4. 외부 서비스: Open-Meteo 날씨·대기질, 네이버 카페 링크, Google News 계열 뉴스.

복제할 때는 원 사이트의 브라우저용 키나 세션을 재사용하기보다, 자체 인증·권한·DB·파일 저장소를 두고 필요한 기능을 자체 API로 제공하는 방식을 권장한다.

## 1. 전체 기능 목록과 데이터 원천

| 영역 | 확인한 기능 | 데이터 원천 | 복제 시 핵심 |
|---|---|---|---|
| 홈 대시보드 | 오늘의 할 일, 오늘의 일정, 빠른 메모, 업무 진행률, 바로가기, 헤드라인 뉴스 | 할 일·일정·메모는 Zustand/localStorage, 뉴스는 API | 단일 기기면 localStorage, 다기기면 자체 CRUD API |
| 날씨·대기질 | 서울 현재 기온·날씨 코드·강수확률, PM10·PM2.5, 7일 예보 | Open-Meteo 외부 API, 30분 localStorage 캐시 | 서버 프록시와 캐시, 좌표·시간대 설정 |
| 인증·설정 | 현재 사용자·역할, 방문 통계, 글자 크기·테마, 알림 권한, 바로가기, 생체 인증, PIN, 로그아웃 | /api/auth/*, /api/stats, localStorage, Web Push | 세션 쿠키와 역할 기반 접근제어를 자체 구현 |
| 근무 | 오늘 근무, 월간 달력, 근무 상태, 사무실 근무표, 임무카드 | 이번 빌드의 정적 번들·이미지 | 일정 JSON/DB와 카드 자산을 직접 운영 |
| 교번 | 날짜별 전체·주간·야간·대기 명단, 시작·종료 시각 | 정적 번들 | roster와 duty assignment 모델 필요 |
| 교번 비교 | 조 1~4, 월 이동, 그룹명·근무자 선택, 개인별 비교 | 정적 번들·브라우저 상태 | 비교 가능한 그룹/근무표 데이터 필요 |
| 5호선 실시간 | 본선·마천·하남 분기, 목록/지도, 새로고침, 자동 갱신 | /api/realtime/trains | 서버 프록시 또는 자체 철도 데이터 공급원 |
| 안전관리 | 운전정보, 사례교육, 열차정보, 위험개소, 안전상식, 주요 위험개소·공지 | /api/safety/*와 Supabase Realtime | 신고·댓글·읽음·상태 전이·파일 저장 구현 |
| 교육 | 새내기, 영상 가이드, 기본업무, 안내방송, 고장조치, 규정, 평가, 내 정보, Railbot | /data/edu/*.json, /api/edu/*, localStorage | 정적 교재와 서버 진도·평가를 분리 |
| 라이프 | 식당 메뉴, 오늘의 운세, 무사고 출근 도장, 젠 분재, ASMR | 메뉴 API, 나머지는 localStorage/클라이언트 | 로컬 기능과 서버 기능을 분리 |
| 게임 | APEX, 반응속도, 사과 먹기, 암산, 색깔 맞추기, 할리갈리, 명예의 전당 | 클라이언트, 일부 랭킹 화면 | 점수 위변조 방지와 별도 랭킹 저장 |
| 온라인 대전 | 오목·오델로 로비와 랭킹, 2인 턴제 대전 UI | 초기 화면에서는 전용 HTTP 호출 미확인 | WebSocket/Realtime, 방·턴·Elo 테이블 필요 |
| 근무 교체 | 매칭 검색, 게시판, 게시·지원·수락·거절·삭제, 실시간 갱신 | Supabase exchange_posts/exchange_volunteers | RLS와 날짜 충돌·상태 전이 검증 |
| 대기충당확인 | 날짜별 사진 등록·확대·삭제, 등록자 표시, 카페 등록 안내 | Supabase public Storage와 목록 메타데이터 | 자체 standby_coverage 테이블·버킷 권장 |
| 생활 보조 | 승용차 운행 시간표, 고덕기지 입고열차, 5호선 주박 위치 | 정적 이미지 | CDN/정적 자산 버전 관리 |
| 힐링카드 | 월 한도, 사용 내역 추가·삭제, 잔액·월별 초기화 | localStorage(Zustand) | 서버 저장 여부를 제품 요구사항으로 결정 |
| 비상 연락처 | 긴급 관제, 승무사업소·기지 전화 링크 | 정적 tel 링크 | 조직 설정값으로 관리하고 최신성 검증 |
| 의견·버그 제보 | 완전 익명 새 제보, 내 대화, 운영자 답글 | /api/feedback*와 브라우저 익명 ID | 익명 ID rate limit, 운영자 권한, 스팸 방지 |

### 홈·업무 대시보드의 로컬 상태

할 일·일정 저장소 이름은 officeDash, 메모 저장소는 diaMemos로 확인되었고, 홈 화면 진입 시 서버 CRUD가 발생하지 않았다. 테마·글자 크기·바로가기·출근 도장·분재·힐링카드·교육 진도도 브라우저 저장소에 저장된다. 관찰된 키는 dia-theme, dia-font-size, diaShortcuts, attendance-stamp-v1, train-dia-bonsai, dia-healing-card, train-dia-edu-progress이다. 이 키는 구현 참고용이며 원 사이트와 호환할 필요는 없다.

### 날씨·대기질

홈 날씨 모듈은 서울의 현재 기온·날씨 코드·강수확률과 PM10·PM2.5를 표시하고 7일 예보를 제공한다. 실제 외부 호출과 캐시 키는 4절에 정리했다.

### 근무·교번의 정적 데이터

근무 화면은 날짜별 주간·야간·비번·휴무, 조, 시각과 임무카드를 보여준다. 교번 비교는 조와 월을 선택해 개인별 근무를 비교한다. 현재 빌드에서는 핵심 근무표가 JavaScript 번들에 포함되어 있고 별도 근무 조회 API가 관찰되지 않았다. 복제 서비스는 다음 자체 모델을 두는 편이 안전하다.

- drivers: 내부 식별자, 표시명, 소속, 역할
- duty_assignments: 날짜, 근무 상태, 조, 시작·종료 시각, 임무 코드
- duty_cards: 날짜·임무별 이미지 또는 문서
- roster_groups: 교번 그룹과 비교 대상

## 2. 사이트 자체 API

아래는 네트워크와 번들에서 확인된 계약이다. 꺾쇠 괄호는 세션 값 또는 리소스 ID 자리표시자이며 실제 사용자 값을 넣지 않았다. 반환 건수와 내용은 날짜·권한에 따라 달라진다.

### 2.1 조회 API

| 메서드 | 경로 | 확인된 응답 형태 | 복제 참고 |
|---|---|---|---|
| GET | /api/auth/me | user 안에 id, name, sabun, personId, role | 세션 유효성·현재 역할 확인용 |
| GET | /api/version | version 문자열 | 클라이언트 캐시·마이그레이션 확인 |
| GET | /api/stats | todayVisitors, todayPosts | 설정 화면 운영 통계. 관리자 권한 적용 |
| GET | /api/news | data[]의 title, link, source, pubDate | Google News RSS 계열 결과를 서버에서 취합하는 형태 |
| GET | /api/life/menu | data[]의 url, kind, name, week, updatedAt | 주차별 메뉴 이미지/PDF 목록 |
| GET | /api/realtime/trains | trains[]의 trainNo, station, destination, direction, status | 전체 결과를 받은 뒤 본선·마천·하남으로 필터링 |
| GET | /api/safety/hazards/counts | data.hazard/action/inspect 각각 count, ids | 안전 배지용 미읽음 수 |
| GET | /api/safety/hazards?sabun=<sabun>&category=<category> | 위험 신고 목록 | category 값으로 action, inspect, hazard가 관찰됨 |
| GET | /api/safety/tips | data[]의 id, title, description, contentType, mediaUrl, thumbnailUrl, createdBy, createdAt | createdBy 최소 공개 |
| GET | /api/edu/videos | videos[]의 id, category, title, url, source | 공개 목록과 운영자 등록 분리 |
| GET | /api/edu/level-records | 평가 기록 배열 | 운전직 세션은 403; 관리자용으로 취급 |
| GET | /api/feedback?anonymous_id=<anonymous_id> | data[]의 익명 제보 스레드 | 본인 익명 ID의 스레드만 조회 |
| GET | /api/feedback/<id>/replies?anonymous_id=<anonymous_id> | 답글 배열 | 스레드 접근 시 익명 ID 검증 |
| GET | /api/admin/dashboard | 관리자 대시보드 데이터 | 관리자 PIN/역할 게이트 |

### 2.2 인증·일반 변경 API

| 메서드 | 경로 | 요청 형태 | 비고 |
|---|---|---|---|
| GET | /api/auth/check-sabun?sabun=<sabun> | 사번 쿼리 | 생체 인증 등록 여부 등 확인 |
| POST | /api/auth/login | JSON sabun, 선택 pin | 성공 시 사용자·세션 반환 |
| GET/POST | /api/auth/webauthn/login | GET은 사번, POST는 userId·credential | WebAuthn challenge와 credential 검증 |
| GET/POST | /api/auth/webauthn/register | GET challenge, POST credential | origin·challenge·사용자 매핑 검증 |
| POST | /api/auth/pin/change | 최초는 newPin·firstSetup, 변경은 currentPin·newPin | 평문 PIN 저장 금지 |
| POST | /api/auth/logout | 본문 없음 | 세션 폐기 |
| POST | /api/stats | 본문 없음 | 홈 진입 시 fire-and-forget 방문 집계 |
| POST | /api/life/menu | multipart file, week, current | 이미지/JPEG 또는 PDF 업로드·교체 |
| DELETE | /api/life/menu?name=<name> | 파일명 쿼리 | Storage 객체와 목록 삭제 |
| POST | /api/feedback | JSON content, anonymous_id | 본문 길이 5~1000자 |
| POST | /api/feedback/<id>/replies | JSON content, anonymous_id | 본인 스레드 또는 운영자 |
| DELETE | /api/feedback?id=<id> | 관리자용 ID 쿼리 | 일반 사용자의 삭제와 분리 |
| POST | /api/alerts | JSON name, sabun, stationFrom, stationTo, direction, message, severity, expiresAt | 활성·만료·작성자 검증 |
| DELETE | /api/alerts?id=<id>&name=<name>&sabun=<sabun> | 식별자 쿼리 | 논리 비활성화 정책 권장 |
| POST | /api/push/subscribe | JSON name, sabun, subscription.endpoint, subscription.keys.p256dh, subscription.keys.auth | Web Push 구독 저장 |
| DELETE | /api/push/subscribe | JSON endpoint | 구독 해제 |
| POST | /api/push/send | JSON name, sabun, title, message | 운영 서버 내부 호출 권장 |

### 2.3 안전 API

코드에서 다음 세부 경로를 확인했다.

- POST /api/safety/hazards: multipart photo, attachment, description, location, name, sabun, category
- PATCH /api/safety/hazards/<id>: JSON description, location, name, sabun, removeFile
- DELETE /api/safety/hazards/<id>: JSON name, sabun
- GET /api/safety/hazards/<id>/comments
- POST /api/safety/hazards/<id>/comments: JSON comment, name, sabun
- PATCH /api/safety/hazards/<id>/comments: JSON commentId, comment, name, sabun
- DELETE /api/safety/hazards/<id>/comments: JSON commentId, name, sabun
- POST /api/safety/hazards/<id>/resolve: JSON resolved, name, sabun
- POST /api/safety/hazards/<id>/reads: JSON sabun, name
- GET /api/safety/hazards/<id>/reads
- GET /api/safety/hazards/<id>/read-status
- POST /api/safety/hazards/<id>/views: 본문 없음
- POST /api/safety/hazards/<id>/likes: JSON name, sabun; 좋아요 토글
- POST /api/safety/tips: multipart title, description, contentType, sabun, name, videoUrl 또는 photo
- POST /api/safety/extract-driving-info: JSON image(base64), mediaType; title, description, location, kind 반환

요청 본문의 이름·사번을 권한 근거로 사용해서는 안 된다. 로그인 세션의 사용자와 대조하고, 파일은 MIME·용량 검사와 악성 파일 검사를 거쳐 제한 버킷에 저장해야 한다.

### 2.4 교육 API

- POST /api/edu/railbot
  - 요청: question, vehicle
  - 응답 모드: need-vehicle(message, options), no-evidence(message), 또는 answer(sources, urgent 포함)
- POST /api/edu/videos: JSON category, title, url
- POST /api/edu/video-views: JSON videoId; 중복 시 duplicate 플래그 사용
- POST /api/edu/level-records: JSON levelId, levelName, score, passed

정적 교육 자료 경로:

- /data/edu/handbook.json
- /data/edu/training.json
- /data/edu/video-guide.json
- /data/edu/handbook-quiz.json
- /data/edu/regulations/operation-rules-quiz.json
- /data/edu/regulations/crew-management-rules-quiz.json
- /data/edu/regulations/operating-staff-rules-quiz.json
- /data/edu/regulations/depot-operation-rules-quiz.json
- /data/edu/regulations/crew-business-rules-quiz.json
- /data/edu/regulations/safety-record-rules-quiz.json
- /data/edu/regulations/detail-operation-rules-quiz.json
- /data/edu/regulations/hr-rules-quiz.json
- /data/edu/regulations/employment-rules-quiz.json

### 2.5 API로 확인하지 못한 기능

- 근무표·교번·교번 비교: 이번 빌드에서는 번들 정적 데이터로 동작해 공식 근무 조회 API를 확인하지 못했다.
- 대기충당확인: 이미지가 Supabase Storage에서 제공되는 것은 확인했지만, 목록 메타데이터의 정확한 REST 테이블/서버 라우트는 이번 성능 기록에서 식별하지 못했다.
- 온라인 오목·오델로: 초기 랭킹/로비에서는 전용 HTTP 호출을 보지 못했다. 대전 시작 후 동적으로 열리는 Realtime 계약은 별도 분석이 필요하다.

## 3. Supabase 직접 사용 영역

관찰된 프로젝트 호스트는 https://uhlxokrskgloupjelqlf.supabase.co 였다. 브라우저 요청에 포함된 anon 키와 Bearer 값은 기록하지 않았다. 복제 서비스는 원 프로젝트 키를 재사용하지 말고 새 프로젝트 또는 자체 백엔드를 사용해야 한다.

### 근무 교체

Supabase JS 호출은 다음 REST 요청과 동등하다.

- GET /rest/v1/exchange_posts?select=*&order=created_at.desc
- GET /rest/v1/exchange_volunteers?select=*&post_id=in.(<post_id 목록>)
- exchange_posts insert: type, requester_id, requester_name, target_id, target_name, dates, requester_dias, target_dias, memo
- 게시글 상태 변경: status를 accepted 또는 declined로 변경하고 필요 시 decline_reason 저장
- exchange_volunteers insert: post_id, person_id, person_name
- 지원 수락: status를 accepted로, accepted_volunteer_id를 지원자 ID로 변경
- 게시글 삭제: 대상 id에 대한 delete

Realtime 채널은 exchange-realtime이며 exchange_posts와 exchange_volunteers 변경을 구독한다. 실제 구현에서는 requester·target·volunteer 본인 여부, 날짜 충돌, 수락·거절 상태 전이를 RLS와 서버 트랜잭션으로 보장해야 한다.

### 안전 알림

알림 목록은 별도 /api/alerts GET보다 Supabase alerts 테이블을 직접 조회하는 코드가 확인되었다. 선택 필드는 id, station_from, station_to, direction, message, severity, created_by, created_at, is_active, expires_at이고 활성 상태와 만료 시각을 클라이언트에서 필터링한다.

Realtime 채널은 alerts-realtime이며 alerts 테이블 변경 이벤트를 구독한다. 복제 시 공지 작성·비활성화 권한을 관리자 또는 승인된 역할로 제한한다.

### Storage

- 식당 메뉴: restaurant-menu/menu/<week>.jpg 또는 PDF
- 대기충당 사진: standby-coverage/<date>/<generated-file>.jpg
- 안전 관련 사진·첨부: 안전 API가 연결한 제한 버킷
- 주박 위치: /notice/jubak/<slug>.png
- 차량 시간표: /images/shuttle-schedule.jpg, /images/depot-schedule.jpg

대기충당 목록의 메타데이터 테이블은 식별하지 못했으므로, 자체 구현에서는 standby_coverage 테이블에 date, storage_path, uploader_id, created_at, deleted_at를 저장하고 Storage 객체와 함께 처리하는 것이 좋다.

## 4. 외부 API·정적 자산

### 날씨·대기질

관찰된 Open-Meteo 호출은 다음과 같다.

    https://api.open-meteo.com/v1/forecast?latitude=37.5665&longitude=126.978&current=temperature_2m,weather_code&daily=precipitation_probability_max&timezone=Asia/Seoul&forecast_days=1
    https://air-quality-api.open-meteo.com/v1/air-quality?latitude=37.5665&longitude=126.978&current=pm10,pm2_5&timezone=Asia/Seoul
    https://api.open-meteo.com/v1/forecast?latitude=37.5665&longitude=126.978&hourly=temperature_2m,weather_code,precipitation_probability&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Asia/Seoul&forecast_days=7

클라이언트는 dia.weather.seoul, dia.weather.forecast.seoul에 약 30분 TTL로 캐시한다. 복제 시 서버 프록시와 짧은 캐시를 두면 호출량과 외부 장애 영향을 줄일 수 있다.

### 뉴스·카페

홈 뉴스는 /api/news를 호출하며 Google News 계열 출처·게시 시각·링크를 표시한다. 뉴스 모달은 약 10분 주기 갱신 안내를 제공한다. 카페 바로가기는 외부 네이버 카페 링크이므로 조직이 승인한 링크만 설정값으로 관리한다.

### 정적 주박·시간표

주박 위치의 슬러그는 hwagok, yeouido, aeogae, wangsimni, gunja, hanamgeomdansan이며 경로 형식은 /notice/jubak/<slug>.png이다. 차량 시간표는 /images/shuttle-schedule.jpg와 /images/depot-schedule.jpg를 이미지 최적화 경로로 표시한다.

## 5. 복제 권장 아키텍처

### 서비스 계층

1. 인증 서비스: 사번 또는 조직 계정, PIN/WebAuthn, 세션 쿠키, 역할.
2. 업무 API: 일정·할 일·메모·근무표·교번 조회/변경.
3. 운영 API: 안전 신고·댓글, 교육 진도, 피드백, 푸시.
4. 실시간 계층: 열차 갱신, 안전 알림, 근무 교체, 온라인 게임.
5. 파일 계층: 메뉴·안전 첨부·대기충당 사진과 메타데이터를 트랜잭션으로 연결.
6. 외부 프록시: Open-Meteo와 뉴스 RSS를 서버에서 호출하고 캐싱.

### 최소 데이터 모델

- 사용자: users, roles, webauthn_credentials, push_subscriptions
- 업무: tasks, schedules, notes, duty_assignments, roster_groups, duty_cards
- 안전: hazard_reports, hazard_comments, hazard_reads, hazard_views, hazard_likes, safety_tips
- 교체: exchange_posts, exchange_volunteers
- 커뮤니케이션: alerts, feedback_threads, feedback_replies
- 교육: edu_videos, video_views, level_records
- 파일: media_objects와 각 업무 테이블의 storage_path

### 캐시·갱신

| 데이터 | 원 사이트에서 관찰한 동작 | 복제 권장 |
|---|---|---|
| 실시간 열차 | 약 30초 주기, 화면 재진입·온라인 복귀 시 갱신 | 서버 수집 10~30초, ETag/last-updated |
| 뉴스 | UI에 약 10분 갱신 안내 | RSS 수집기 10분 캐시, 실패 시 직전 결과 |
| 날씨·대기질 | localStorage 약 30분 TTL | 서버·브라우저 30분 캐시 |
| 메뉴 이미지 | 주차별 Storage 객체 | week unique 제약과 교체 이력 |
| 안전 알림·근무 교체 | Realtime 변경 이벤트 | 초기 REST + 이후 이벤트 구독, 만료 시각 서버 필터 |

### 보안·개인정보

- 요청 본문의 name·sabun을 권한 근거로 사용하지 말고 세션 사용자와 비교한다.
- Supabase anon 키는 RLS의 대체물이 아니다. 서비스 역할 키는 서버 환경변수에만 둔다.
- 사진·첨부·WebAuthn credential·Push subscription 키는 로그와 보고서에서 마스킹한다.
- 익명 제보는 이름·사번을 수집하지 않는다는 UI 약속을 유지하고 rate limit·스팸 방지를 둔다.
- 안전 신고·교대 게시판·통계는 역할별 읽기/쓰기/삭제 정책과 감사 로그가 필요하다.

## 6. 기능 누락 재점검 결과

아래 체크리스트를 화면의 홈 바로가기, 근무 탭, 안전 탭, 교육 메뉴, 라이프 메뉴, 더보기 메뉴, 모달, 네트워크 요청, 동적 청크에서 다시 대조했다.

- [x] 홈: 할 일, 일정, 빠른 메모, 진행률, 일정관리, 오늘의 할일, 이번주 일정, 메모
- [x] 홈 부가기능: 식당 메뉴, 대기충당확인, 카페 바로가기, 헤드라인 뉴스
- [x] 홈 환경 정보: 현재 날씨·강수확률, 대기질, 7일 예보
- [x] 홈 설정: 테마, 글자 크기, 바로가기, 알림 권한, 생체 인증, PIN, 로그아웃, 통계
- [x] 근무 화면: 홈, 근무, 달력, 교번, 5호선, 더보기 탭
- [x] 근무·달력: 오늘 근무, 월간 달력, 상태 요약, 사무실 근무표, 임무카드
- [x] 교번: 날짜 선택, 전체·주간·야간·대기 필터, 근무자·시간 목록
- [x] 교번 비교: 조 1~4, 그룹명, 월 이동, 근무자 선택
- [x] 5호선 실시간: 본선·마천·하남, 목록/지도, 새로고침, 자동 갱신
- [x] 안전: 운전정보, 사례교육, 열차정보, 위험개소, 안전상식, 위험 신고·댓글·읽음·조회·좋아요·해결
- [x] 안전 팁·알림: 이미지/동영상 팁, 활성 알림, 심각도·만료·Realtime
- [x] 교육: 새내기, 영상 가이드, 기본업무, 안내방송, 고장조치, 규정, 평가, 내 정보, Railbot
- [x] 라이프: 식당 메뉴, 운세, 출근 도장, 분재, ASMR
- [x] 게임: APEX, 반응속도, 사과 먹기, 암산, 색깔 맞추기, 할리갈리, 명예의 전당
- [x] 온라인 대전: 오목, 오델로, 랭킹 화면
- [x] 더보기: 교번 비교, 근무 교체, 승용차 운행 시간표, 고덕기지 입고열차, 5호선 주박위치, 힐링카드, 비상 연락처
- [x] 근무 교체: 매칭 검색, 게시판, 게시·지원·수락·거절·삭제
- [x] 대기충당확인: 목록, 사진 확대, 등록 진입, 삭제 진입, 카페 안내
- [x] 의견·버그 제보: 익명 새 제보, 내 대화, 답글
- [x] PWA 운영 요소: 버전 표시, 온라인/오프라인 재진입 시 실시간 갱신, Web Push 구독

재점검 결과, 조사한 화면에 노출된 사용자 기능은 위 목록과 본문에 모두 반영했다. 단, 온라인 대전의 실제 플레이 프로토콜과 대기충당 메타데이터 REST 경로는 초기 화면에서 호출되지 않아 별도 심층 세션이 필요하다. 또한 관리자 전용 메뉴·응답은 일반 운전직 세션으로 상세 화면까지 확인할 수 없었다.

## 7. 재현 가능성 및 한계

- 이 보고서는 2026-08-18에 노출된 v3.8.1 빌드의 관찰 결과다. 날짜별 근무표, 뉴스, 메뉴, 열차 결과는 바뀔 수 있다.
- 관리자 전용 응답의 상세 스키마와 변경 요청의 성공·실패 메시지는 실행하지 않고 코드 계약만 확인했다.
- 번들 근무표·교육 교재·정적 이미지는 서버 API가 아니므로 원 사이트 API를 호출하는 것만으로 동일 기능을 얻을 수 없다.
- 원 사이트의 내부 API와 Supabase 테이블은 공개적 안정 계약으로 보장된다고 볼 수 없다. 복제 서비스는 자체 API 추상화 계층과 외부 소스 장애 대응을 둬야 한다.
- 개인 정보와 저작권이 있는 교재·이미지·뉴스를 복제할 때는 조직의 사용 권한과 보존 정책을 확인해야 한다.

## 결론

직접 확인 가능한 핵심 조회 API는 /api/auth/me, /api/news, /api/life/menu, /api/realtime/trains, /api/safety/*, /api/edu/*, /api/feedback*이다. 근무표·교번·생활 미니 기능은 정적 JSON·번들·localStorage에 의존하고, 근무 교체·알림·파일은 Supabase REST/Realtime/Storage 조합이다.

실제 복제 프로젝트에서는 위 경로를 그대로 외부 호출하기보다 인증·RLS가 적용된 자체 백엔드가 같은 개념의 API를 제공하고, 열차·날씨·뉴스만 허용된 외부 소스의 서버 프록시로 연결하는 구성이 가장 안정적이다.
