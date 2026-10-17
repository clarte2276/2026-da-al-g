# LLM 초안 평가 사례 전문가 검수 기록

## 검수자

- 이름: 이용호
- 소속: 서울교통공사
- 직책: 차장
- 검수일: 2026-10-17

## 범위

`paper/data/human_review_checklist.md`에 수록된 `llm_drafted` 사례 20건을 검수했다. `existing_v2` 사례 17건은 이번 검수 범위에 포함하지 않았다.

- `graph_704_bus_failure`
- `graph_acm_start_failure`
- `graph_single_cm_failure`
- `graph_siv_start_failure`
- `graph_master_controller_failure`
- `graph_all_cm_failure`
- `graph_single_door_open_failure`
- `graph_all_doors_close_failure`
- `graph_one_car_doors_close_failure`
- `graph_air_pipe_rupture`
- `graph_parking_brake_release_failure`
- `graph_inverter_output_half`
- `graph_front_tc1_failure`
- `graph_rear_safety_brake_dispatch`
- `graph_front_safety_brake_rescue`
- `wind_threshold_report`
- `fog_station_duties`
- `earthquake_warning_threshold`
- `earthquake_control_initial_stop`
- `earthquake_driver_speed`

## 방법 및 결과

단일 철도 운영기관 현업 전문가가 체크리스트 기반으로 검수했다. 체크리스트는 질문 현실성, 정답 근거 정확성, 참조 답변 정확성, 링크 필요성을 다뤘다. 20건 모두 OK 판정을 받았으며 수정 0건, 삭제 0건이다.

## 한계

검수자는 1명이므로 평가자 간 일치도를 산출하지 않았다. 검수자는 링크 구조를 알고 있었으며 블라인드 검수가 아니었다. 이 기록은 `llm_drafted` 20건에만 해당하고 기존 `existing_v2` 17건은 검수하지 않았다.
