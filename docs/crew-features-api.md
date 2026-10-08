# 승무원 부가기능 API 계약 (dia5.kr 기능 이식)

백엔드(`back/app/crew.py`)와 사용자 앱(`front/user`)이 공유하는 계약이다. 모든 경로는 `/api` 아래, 인증은 기존 Bearer 세션(`CurrentUser`), 관리자 전용은 `AdminUser`.
"나"는 항상 세션 사용자(`user.display_name`)로 판단한다. 요청 본문의 이름은 권한 근거로 쓰지 않는다.
시각은 ISO 8601(UTC), 날짜는 `YYYY-MM-DD`. 오류는 FastAPI 기본 `{"detail": "..."}`.

## 1. 근무 교체 (exchange)

Post: `{id, type: "direct"|"open", status: "open"|"accepted"|"declined"|"cancelled", requester_name, target_name|null, dates: [date], requester_dias: [code], target_dias: [code], memo, decline_reason|null, accepted_volunteer_id|null, volunteers: [Volunteer], created_at, mine: bool}`
Volunteer: `{id, person_name, status: "pending"|"accepted"|"rejected", created_at}`

| 메서드 | 경로 | 본문 | 규칙 |
|---|---|---|---|
| GET | /exchange/posts?status=&mine=true | | 최신순. mine=true면 내가 요청자·대상·지원자인 글만 |
| POST | /exchange/posts | `{type, target_name?, dates, requester_dias, target_dias?, memo?}` | direct는 target_name 필수, 자기 자신 불가. dates 1~7개 |
| POST | /exchange/posts/{id}/respond | `{action: "accept"|"decline", reason?}` | direct + open 상태 + 대상자 본인만 |
| POST | /exchange/posts/{id}/volunteers | `{}` | open 타입 + open 상태, 요청자 아닌 사람, 중복 불가 |
| POST | /exchange/posts/{id}/volunteers/{vid}/accept | | 요청자만. 글 accepted, 나머지 지원자 rejected |
| DELETE | /exchange/posts/{id} | | 요청자 또는 관리자. status=cancelled (소프트) |
| GET | /exchange/match?date=&kind=day|night|off|rest|standby | | 그 날짜 근무표에서 kind가 일치하는 기관사 `[{name, code, type}]` (본인 제외). 근무표 없으면 [] |

## 2. 대기충당확인 (standby coverage)

Item: `{id, date, uploader_name, created_at, mine: bool, image_url: "/api/standby-coverage/{id}/image"}`

| GET | /standby-coverage?date= | | date 생략 시 최근 50건 |
| POST | /standby-coverage | multipart `date`, `file`(jpg/png/webp, 10MB 이하) | 저장: `storage_root/standby/<date>/<uuid>.<ext>` |
| GET | /standby-coverage/{id}/image | | 이미지 바이트 |
| DELETE | /standby-coverage/{id} | | 올린 사람 또는 관리자, deleted_at 소프트 삭제 |

## 3. 안전

Alert: `{id, station_from, station_to, direction: "up"|"down"|null, message, severity: "info"|"warning"|"danger", created_by, created_at, expires_at|null}`

| GET | /alerts | | 활성 + 미만료만 |
| POST | /alerts | Alert 필드(id/created_* 제외) | 관리자 |
| DELETE | /alerts/{id} | | 관리자, is_active=false |

Hazard: `{id, category: "hazard"|"action"|"inspect", title, description, location, status: "open"|"in_progress"|"resolved", author_name, created_at, comment_count}`; 상세는 `comments: [{id, author_name, content, created_at}]` 추가.

| GET | /safety/hazards?category= | | 최신순 |
| GET | /safety/hazards/{id} | | 상세 + 댓글 |
| POST | /safety/hazards | `{category, title, description, location?}` | |
| POST | /safety/hazards/{id}/comments | `{content}` | 1~1000자 |
| PATCH | /safety/hazards/{id} | `{status}` | 관리자 |

Tip: `{id, title, description, media_url|null, created_at}` — GET /safety/tips, POST /safety/tips(관리자), DELETE /safety/tips/{id}(관리자).

## 4. 익명 의견·버그 제보 (voice)

이름·사번을 저장하지 않는다. 소유 판별은 `owner_hash = sha256(user.id)`만 저장.
Thread: `{id, content, created_at, replies: [{id, content, from_admin: bool, created_at}]}`

| GET | /voice | | 내 스레드만 |
| POST | /voice | `{content}` 5~1000자 | 사용자당 10분 5건 제한(429) |
| POST | /voice/{id}/replies | `{content}` | 본인 스레드 또는 관리자 |
| GET | /admin/voice | | 관리자, 전체 |

## 5. 라이프·정보

| GET | /news | | Google News RSS("서울교통공사 6호선") 10분 캐시, `[{title, link, source, published}]`, 실패 시 직전 결과 또는 [] |
| GET | /life/menu | | `[{id, week, filename, created_at, url: "/api/life/menu/{id}/file"}]` 최신순 |
| POST | /life/menu | multipart `week`(예 2026-W41), `file`(이미지/PDF) | 관리자, 같은 week는 교체 |
| GET | /life/menu/{id}/file | | 파일 바이트 |
| GET | /contacts | | `[{name, phone, group}]` 관리자가 등록한 비상 연락처 |
| PUT | /contacts | `[{name, phone, group}]` | 관리자, 전체 교체 |
| GET | /edu/videos | | `[{id, category, title, url, created_at}]` |
| POST | /edu/videos | `{category, title, url}` | 관리자 |
| DELETE | /edu/videos/{id} | | 관리자 |
| GET | /realtime/trains | | 서울 열린데이터 realtimePosition(6호선). env `SEOUL_SUBWAY_API_KEY` 없으면 503 `"실시간 열차 API 키가 설정되지 않았습니다"`. 20초 캐시. `[{train_no, station, direction: "up"|"down", status, terminal, updated_at}]` |
| POST | /games/scores | `{game, score}` | game ∈ reaction, math, color. score 정수 |
| GET | /games/scores?game= | | 사람별 최고점 상위 20 `[{name, score, created_at}]`. reaction은 낮을수록 좋음 |

날씨·대기질은 앱이 Open-Meteo를 직접 호출한다(백엔드 없음). 할 일·일정·빠른 메모·힐링카드는 기기 로컬(SharedPreferences)에만 저장한다.

## 6. 범위 밖

온라인 오목·오델로 대전(실시간 방/턴 상태)은 이번 범위에 포함하지 않는다.
