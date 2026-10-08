# 6호선 행로표 + 근무계획 백엔드 (TASK A)

## 변경 파일
- `back/app/duty.py` (신규): 행로표 파서 `parse_route_xlsx`, 근무계획 파서 `parse_duty_xlsx`, 코드 분류 `classify`, 읽기 시점 병합 `merge_routes`.
- `back/app/models.py`: `DutyRoute` 테이블(`duty_routes`: id, effective_date(unique), data JSON, source_filename, updated_at). `create_all`로 생성되며 SQL 마이그레이션은 추가하지 않음(`duty_schedules`도 같은 방식).
- `back/app/management.py`: 파서 코드를 `duty.py`로 옮김(`management.parse_duty_xlsx`는 그대로 import 가능). `GET/POST /api/admin/duty-routes` 추가, `GET /api/duty/{month}`에서 최신 행로표를 병합.
- `back/scripts/load_duty.py` (신규): `data/근무계획/*.xlsx`(행로표 + 월별 근무계획)를 로컬 DB에 적재. `python -m scripts.load_duty [폴더]`.
- `back/tests/test_management.py`: 코드 분류 테스트, 실제 10월 근무계획과 행로표를 파싱하는 테스트, 업로드 엔드포인트 테스트 추가(`data/` 폴더가 없으면 건너뜀).
- `front/admin/src/management.jsx`: 근무표 섹션에 행로표 업로드 폼을 추가함(상태 1줄 + 폼 1개).

## 행로표 파서
- 시트와 sheetKind 매핑: `평일, 평평240801`→`평평`, `평휴240801`→`평휴`, `휴평240801`→`휴평`, `휴일,휴휴`→`휴휴`. 작업용 시트와 이전 버전 시트는 읽지 않음.
- 왼쪽 A..N 열(수색)만 읽고 O열부터 시작하는 신내 블록은 무시함.
- 요약표(AD..AQ)는 평휴와 휴평 시트에 **없음**. 그래서 네 시트 모두에서 Dia 블록 자체를 파싱함. 블록은 `출근시각` 라벨에서 시작해 `근무시간` 머리글 행에서 끝남.
  - 출근 시각은 라벨 아래 A열의 첫 시각, Dia 번호는 A열의 첫 숫자(`26\n통상`, `73\n안암` 같은 값도 처리), 퇴근 시각은 머리글 다음 두 행의 A열에서 읽음.
  - 머리글 다음 1~2행에는 운전1~3과 대기1~2의 종료/시작 시각이 들어 있음. 3행째에는 근무시간, 운전합계, 대기합계 등 소요시간이 들어 있음.
  - 근무시간이 비어 있거나 0인 블록(평평:72, 휴휴:72 같은 빈 자리)은 건너뜀.
- 시각 값은 `str`, `time`, `timedelta`(24h를 넘는 값 포함) 모두 초 단위로 정규화한 뒤 `HH:MM`로 출력함(초는 버림). 퇴근 시각이 출근 시각보다 이르면 `nextDay=true`.
- **검증**: `평평`과 `휴휴` 시트는 요약표가 있어서 블록 파싱 결과의 depart/arrive/workMinutes/driveMinutes/standbyMinutes를 요약표 행 하나하나와 비교함. 값이 있는 행은 모두 일치함. 요약표에서 빠진 행은 Dia 번호만 있고 값이 비어 있는 행뿐임. 또한 모든 턴에서 run 세그먼트 시간의 합이 운전합계와 3분 이내로 일치함.

### 턴 수
| sheetKind | 턴 수 | 세그먼트가 있는 턴 |
|---|---|---|
| 평평 | 43 (주간 1–23, 26–29 통상, 야간 61–71, 73–77) | 43 |
| 휴휴 | 33 | 33 |
| 평휴 | 16 (61–71, 73–77) | 16 |
| 휴평 | 16 | 16 |
| **합계** | **108** | **108** |

### 세그먼트 (최선 노력, 한계 있음)
- 세그먼트는 블록 하단 표의 **운전1~3 구간(`run`)과 대기1~2 구간(`standby`)**에서 만들기 때문에 시각은 정확함.
- 그려진 열차 그림을 열차 단위로 쪼개지는 **않음**. 그래서 run 하나가 열차 여러 대에 걸칠 수 있음(예: 주간 Dia는 대부분 DMC→DMC). `train`은 첫 열차의 번호이고, `from`/`to`는 시작/종료 시각이 적힌 셀의 열을 역으로 매핑한 값임(C 응암, E/F DMC, G/H 공덕, I/J 안암, K/L 봉화산, M 신내기지).
- `dir`은 역 순서(응암→신내기지 = up)로 정함. 출발역과 도착역이 같으면 null.
- 열차 번호를 찾지 못한 run: 평평:2, 그리고 시트별 Dia 77(5건). 출발역이 null인 run은 5건, 도착역이 null인 run은 1건.
- 출고·입고·편승·교대 종류의 세그먼트는 아직 만들지 않음. 이를 위해서는 열차 그림을 열차 단위로 파싱하는 작업이 필요함.
- `break` = 대기 구간 `"HH:MM~HH:MM"`(구간이 여러 개면 쉼표로 구분), `route` = run 구간의 역을 차례로 이은 문자열, `firstRun` = 첫 run의 출발 시각.

## 근무계획 파서
- `교번근무계획(지정근무반영)` 시트를 우선 사용함. 열 위치는 머리글에서 찾음(`승무원`, `…사원번호`, `N일`). 시트가 없으면 기존 `교번기관사 근무계획` 양식을 사용함(기존 동작과 기존 테스트 유지).
- 드라이버마다 `empNo`(문자열)를 추가함. office는 `수색승무사업소`, line은 `6호선`.
- 코드 분류는 `duty.classify`가 담당하며 테스트로 확인함. `비`, `N~`, `대N~`→off / `휴N`, `운휴N`, `대휴N`, `휴N~`→rest / `대N`→standby / `지정…`, `주간`, `보완교육`→designated / 60 미만 숫자→day, 60 이상 숫자→night / 그 밖의 값과 빈칸→unknown.
- 빈칸 처리: 8월 파일에는 근무 코드가 비어 있는 셀이 있음(207칸, 휴직자 등). 새 양식에서는 이를 오류로 처리하지 않고 `code:""`, `type:"unknown"`으로 둠. 기존 양식은 지금처럼 오류로 처리함.
- 공휴일: 같은 통합문서의 `공휴일` 시트 A열 날짜와 토·일요일로 평/휴를 계산함. 결과는 `dayTypes`에 D-1부터 말일 다음 날(D+1)까지 저장함.
- 5개월 파싱 결과: 6월 94명, 7월 93명, 8월 101명, 9월 94명, 10월 94명. 8월의 빈칸을 빼면 unknown은 0건임. 모든 달에서 `turnKey`와 `continues`가 행로표 턴에 100% 매칭됨.

## GET /api/duty/{month} 병합 (읽기 시점)
- 각 날짜에 `dayType`과 `turnKey`를 붙임. `N~` 코드(N≥60)에는 `continues`도 붙음.
  - day: `평평:N`(평일) 또는 `휴휴:N`(휴일)
  - night: `<D의 평/휴><D+1의 평/휴>:N`
  - 야간대기(`대N`, N≥60)는 dayType만 두 글자 조합이고 turnKey는 null
- 참조된 턴만 `turns`에 포함하며, 행로표가 있으면 `turnDetailIsDummy=false`임. 행로표가 없으면 기존 동작과 같음.
- 행로표는 effective_date가 가장 늦은 것 하나를 사용함. 여러 개정본을 월별로 고르는 기능은 아직 없음.

## 샘플 턴 (`평평:70`)
```json
{
  "id": "70", "type": "night", "dayType": "평평",
  "depart": "21:16", "arrive": "09:18", "nextDay": true,
  "firstRun": "21:46", "break": "01:56~06:28", "route": "DMC→신내기지→DMC", "trainNo": "6299",
  "workMinutes": 689, "driveMinutes": 269, "standbyMinutes": 240,
  "segments": [
    {"kind": "run", "train": "6299", "from": "DMC", "to": "신내기지", "dep": "21:46", "arr": "00:56", "dir": "up", "nextDay": false},
    {"kind": "standby", "train": null, "from": "신내기지", "to": "신내기지", "dep": "01:56", "arr": "06:28", "dir": null, "nextDay": true},
    {"kind": "run", "train": "6060", "from": "신내기지", "to": "DMC", "dep": "07:28", "arr": "08:48", "dir": "down", "nextDay": true}
  ]
}
```

병합된 날짜 예시 (10월, 가동훈):
`"2026-10-02": {"code":"70~","type":"off","turn":null,"dayType":"평","turnKey":null,"continues":"평평:70"}`

## 검증
`cd back && .venv/Scripts/python -m pytest -q` → 49 passed. `python -m scripts.load_duty`로 로컬 SQLite에 5개월치와 행로표 108턴을 적재함.
