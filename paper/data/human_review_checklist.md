# Human review checklist

Review each LLM-drafted case against the cited source fragments. The 15 graph rows pair direct guide evidence (`via_link=false`) with approved-link article evidence (`via_link=true`); the five document-only rows need no graph link and use a regulation article directly. The short reason states why both graph ends are needed or why a document-only case needs no link.

| Name | Question | Gold labels | Why the link is needed |
|---|---|---|---|
| `graph_704_bus_failure` | 6호선 전동차의 직류모선 704선 가압불능 시 재기동 절차와 전부Tc차 기동불능 상황의 보고 방법은 무엇인가요? | 6호선 전동차고장조치 길라잡이-1.pptx slide 32 (direct); 운전취급규정 제35조 (via link) | 슬라이드 32의 고장별 점검·재기동 절차와 제35조의 운전관제 보고 의무가 각각 필요하다. Link ID: `01743119-db72-4c3e-8304-19ff915262dc`. |
| `graph_acm_start_failure` | M1차(2호, 6호) 보조공기압축기(ACM)가 구동불능이면 어떤 차단기와 접촉기를 확인하고, 복귀되지 않으면 어떻게 해야 하나요? | 6호선 전동차고장조치 길라잡이-1.pptx slide 34 (direct); 운전취급규정 제35조 (via link) | 슬라이드 34가 ACM 전용 차단기·접촉기 조치를, 제35조가 운전 지장 우려 시 보고 의무를 담는다. Link ID: `5dda2382-f596-4854-862c-34bca6b39c48`. |
| `graph_single_cm_failure` | M2차(3호, 7호) 1개 UNIT 주공기압축기(CM) 구동불능 시 과열 기준과 차단기 확인, 운행 조치는 무엇인가요? | 6호선 전동차고장조치 길라잡이-1.pptx slide 40 (direct); 운전취급규정 제35조 (via link) | 슬라이드 40의 M2차 차단기·과열·차량교환 절차와 제35조의 운전관제 보고 의무가 함께 답에 필요하다. Link ID: `9870c1d8-fa69-414b-b360-0e929b3efac8`. |
| `graph_siv_start_failure` | 보조전원장치(SIV) 기동불능 때 관제 보고 후 연장급전 여부에 따라 어떤 순서로 조치하나요? | 6호선 전동차고장조치 길라잡이-1.pptx slide 42 (direct); 운전취급규정 제35조 (via link) | 슬라이드 42의 SIV별 연장급전·부하감소 절차와 제35조의 승무원 보고 의무를 함께 확인해야 한다. Link ID: `86be0452-728f-4c3e-ba34-d27c51908975`. |
| `graph_master_controller_failure` | 정거장 도중에 정차한 열차의 주간제어기 출력전압 이상이 RESET으로 복구되지 않아 구원운전할 때 후부Tc차 운전과 구원열차 도착까지의 이동 제한은 무엇인가요? | 6호선 전동차고장조치 길라잡이-1.pptx slide 44 (direct); 운전취급규정 제315조 (via link) | 슬라이드 44의 후부Tc차·구원차 운전 절차와 제315조의 구원 요구 후 이동 제한이 각각 필요하다. Link ID: `359403f2-b9d8-4344-83ac-6c0ed94eb52d`. |
| `graph_all_cm_failure` | 전체 차량의 주공기압축기(CM) 구동불능으로 정거장 도중에 정차해 구원을 요청했을 때 MR 압력 기준과 운행 조치, 열차 이동 조건은 무엇인가요? | 6호선 전동차고장조치 길라잡이-1.pptx slide 38 (direct); 운전취급규정 제315조 (via link) | 슬라이드 38의 전체 CM 장애 조치와 제315조의 구원 후 이동 제한을 함께 적용해야 한다. Link ID: `30cb64b0-a721-414d-8a84-2e1044dec5eb`. |
| `graph_single_door_open_failure` | 6호선에서 한 개 출입문 열림불능일 때 현장 점검과 잠금·안전막·감시자·차량교환역 운행은 어떻게 하며, 제328조는 어떤 일반 조치를 정하나요? | 6호선 전동차고장조치 길라잡이-1.pptx slide 54 (direct); 운전취급규정 제328조 (via link) | 슬라이드 54의 단일 출입문 현장 조치와 제328조의 보고·방송·응급조치·회송 규정을 함께 비교해야 한다. Link ID: `3ca1ba21-69c8-4fb9-8195-b5464339ba0c`. |
| `graph_all_doors_close_failure` | 전체 출입문 닫힘불능으로 출입문대표등이 소등되면 닫힘 제어 순서와 계속 불능일 때의 회송 조치는 무엇인가요? | 6호선 전동차고장조치 길라잡이-1.pptx slide 58 (direct); 운전취급규정 제328조 (via link) | 슬라이드 58의 전차량 닫힘 제어와 바이패스 절차, 제328조의 일반 회송 기준을 함께 써야 한다. Link ID: `a9ec9af7-9d02-424f-a52e-0857cf10026e`. |
| `graph_one_car_doors_close_failure` | 한 량의 출입문 닫힘불능이 발생하면 해당차와 인접차를 어떻게 RESET하고, 계속 불능일 때 어떤 회송 조치를 하나요? | 6호선 전동차고장조치 길라잡이-1.pptx slide 60 (direct); 운전취급규정 제328조 (via link) | 슬라이드 60의 해당·인접차 CC RESET과 바이패스 조치, 제328조의 회송 기준이 모두 필요하다. Link ID: `d7d11e9c-6b9d-4b49-93d6-c8c9fa01a8c1`. |
| `graph_air_pipe_rupture` | 정거장 외에서 통기불능이 된 6호선 6300호 M2차 주공기관 또는 CM 호스 파열 시 MR 콕크와 제동장치 취급, 규정상 운전은 어떻게 하나요? | 6호선 전동차고장조치 길라잡이-2.pptx slide 9 (direct); 운전취급규정 제327조 (via link) | 슬라이드 9의 6300호 분기별 콕크·스위치 순서와 제327조의 통기불능 운전 조건이 필요하다. Link ID: `b7076091-3dd9-4892-b423-8a1ffb937af2`. |
| `graph_parking_brake_release_failure` | 정거장 외 주공기관 파열로 통기불능이고 주차제동이 풀리지 않으며 MR 압력이 3.5 kg/㎠ 이하일 때 어떤 순서로 풀고, 운전·회송은 어떻게 결정하나요? | 6호선 전동차고장조치 길라잡이-2.pptx slide 11 (direct); 운전취급규정 제327조 (via link) | 슬라이드 11의 MR압력별 제동 해제·회송 순서와 제327조의 통기불능 운전 조건이 필요하다. Link ID: `8130d459-9650-4329-8abe-4c6932e2be4c`. |
| `graph_inverter_output_half` | 6호선 운행 중 인버터장치 출력이 반감(1/2)되고 VVVF 2개가 NG일 때 점검할 차단기와 수동운전 전환 승인은 무엇인가요? | 6호선 전동차고장조치 길라잡이-2.pptx slide 25 (direct); 운전취급규정 제330조 (via link) | 슬라이드 25의 인버터별 차단기와 관제 지시, 제330조의 5~8호선 자동운전 원칙·수동운전 예외·모드변경 승인이 필요하다. Link ID: `17bbef3c-7b0d-41c7-8115-61068753089a`. |
| `graph_front_tc1_failure` | 전부 TC1 고장이 RESET으로 복구되지 않아 TC2로 비상운전하고 지령식을 시행할 때 어떤 조치와 확인을 하나요? | 6호선 전동차고장조치 길라잡이-2.pptx slide 29 (direct); 운전취급규정 제142조 (via link) | 슬라이드 29의 TC1 RESET·TC2 비상운전과 제142조의 지령식 시행 요건을 함께 답해야 한다. Link ID: `698c77ee-04e9-429d-87cd-ab3612fe2586`. |
| `graph_rear_safety_brake_dispatch` | 후부Tc차 보안제동 S/W 풀림불능을 자력운전할 때 확인 순서와 지령식 운전 속도·시행 조건은 무엇인가요? | 6호선 전동차고장조치 길라잡이-2.pptx slide 19 (direct); 운전취급규정 제142조 (via link) | 슬라이드 19의 Tc차·운전실 취급 및 45km/h 제한과 제142조의 지령식 시행 전 확인·통보 조건을 함께 써야 한다. Link ID: `0a47f811-f0be-458b-94d4-e613f27e318d`. |
| `graph_front_safety_brake_rescue` | 정거장 도중에 정차한 전동차에서 전부Tc차 보안제동 S/W 풀림불능으로 구원열차를 요구할 때 연결 준비, 양쪽 운전실 취급, 구원 도착 전 이동 제한은 무엇인가요? | 6호선 전동차고장조치 길라잡이-2.pptx slide 18 (direct); 운전취급규정 제315조 (via link) | 슬라이드 18의 보안제동 고장차·구원차 설정과 제315조의 구원열차 도착 전 이동 제한이 함께 답에 필요하다. Link ID: `a3219067-c8a7-46b5-9cd5-fd923ce33116`. |
| `wind_threshold_report` | 폭풍 풍속이 매초 20m 이상으로 판단되면 누가 관제에 보고하고, 풍속 구간별 지상열차 운전은 어떻게 규제하나요? | 운전취급규정 제347조 (direct; `via_link=false`) | 제347조만으로 답할 수 있는 문서 전용 사례이며 교차문서 링크가 필요하지 않다. |
| `fog_station_duties` | 안개나 눈보라로 시계가 나쁘고 통신기능까지 불통일 때 역장 또는 소장은 어떤 보고·선로·열차진입 조치를 해야 하나요? | 운전취급규정 제350조 (direct; `via_link=false`) | 제350조만으로 답할 수 있는 문서 전용 사례이며 교차문서 링크가 필요하지 않다. |
| `earthquake_warning_threshold` | 지진 진도 3부터 7까지의 예보·경보·비상경보 발령 기준과 현상은 어떻게 구분하나요? | 운전취급규정 제354조 (direct; `via_link=false`) | 제354조의 경보 기준표만으로 답할 수 있는 문서 전용 사례이며 교차문서 링크가 필요하지 않다. |
| `earthquake_control_initial_stop` | 지진이 발생했을 때 운전관제는 운행 중인 열차를 어떻게 취급하고 어떤 경보를 발령해야 하나요? | 운전취급규정 제355조 (direct; `via_link=false`) | 제355조만으로 답할 수 있는 문서 전용 사례이며 교차문서 링크가 필요하지 않다. |
| `earthquake_driver_speed` | 지진을 감지하거나 통보받은 기관사의 정차 후 주의운전 속도와 다음 정거장 진입 기준은 무엇인가요? | 운전취급규정 제356조 (direct; `via_link=false`) | 제356조의 지진상황별 절차만으로 답할 수 있는 문서 전용 사례이며 교차문서 링크가 필요하지 않다. |
## Link-selection queries

Executed read-only against the shared SQLite database. The status count returned 36 approved rows in this worktree; the task brief expected 37.

Count by status:

```sql
SELECT status, count(*) n
FROM document_links
GROUP BY status;
```

Approved-link source/target selections and text used to choose the cases:

```sql
SELECT l.id,l.note,l.source_selection,l.target_selection,
       sv.id source_version,sd.filename source_doc,sc.kind source_kind,
       sc.text source_text,sc.pages source_pages,tv.id target_version,
       td.filename target_doc,tc.kind target_kind,tc.text target_text,tc.pages target_pages
FROM document_links l
JOIN document_versions sv ON sv.id=l.source_version_id
JOIN documents sd ON sd.id=sv.document_id
LEFT JOIN document_contents sc ON sc.version_id=sv.id
JOIN document_versions tv ON tv.id=l.target_version_id
JOIN documents td ON td.id=tv.document_id
LEFT JOIN document_contents tc ON tc.version_id=tv.id
WHERE l.status='approved'
ORDER BY sd.filename,td.filename,l.created_at,l.id;
```

Only the 15 link IDs listed above were used for new cases; each ID appears once. No retrieval output was used to select or tune questions.
