# 사용자 소견 표준 용어 초안

대상: DustUp 검색 후보 2,711건. 원문에서 확인한 현상과 팀 요구를 바탕으로 제안한 43개 용어입니다.

원본의 고장 분류와 신규 접수 소견은 다릅니다. 아래 표준 용어의 빈도를 전체 데이터에서 집계한 것은 아닙니다. 입력에 실제 표현된 내용만 선택합니다.

흡입구 먼지 과다, 외장 찌그러짐, 외장 잔금·균열은 팀 시나리오에서 추가한 용어입니다. 유사한 넓은 분류가 있다는 이유로 원문에 해당 조건이 있었다고 표시하지 않았습니다.

## 표준 값

| 범위 | 코드 | 표준 값 | 자연어 예시 | 근거 사례 ID |
|---|---|---|---|---|
| 전원·충전 | `POWER_NO_START` | 전원 켜짐 불가 | 전원을 눌러도 아무 반응이 없어요 | rcint_10275 |
| 전원·충전 | `POWER_INTERMITTENT` | 작동 중 간헐적 꺼짐 | 쓰다가 가끔 꺼져요 | rcint_25599, restart_7674 |
| 전원·충전 | `STOP_AFTER_START` | 시작 직후 정지 | 조금 움직이다가 바로 멈춰요 | anstiftung_6772, rcint_31607 |
| 전원·충전 | `CHARGING_FAILURE` | 충전 불가 | 충전기에 꽂아도 충전이 안 돼요 | anstiftung_2593 |
| 전원·충전 | `CHARGING_INTERMITTENT` | 충전 접속 불안정 | 충전 단자 연결이 됐다 안 됐다 해요 | rcint_18011 |
| 전원·충전 | `BATTERY_FAST_DRAIN` | 배터리 빠른 방전 | 배터리가 너무 빨리 닳아요 | rcint_14280 |
| 전원·충전 | `BATTERY_NORMAL` | 배터리 정상 보고 | 점검해 보니 배터리는 정상이에요 | rcint_31607, anstiftung_1772 |
| 흡입·공기 흐름 | `SUCTION_WEAK` | 흡입력 저하 | 예전보다 잘 못 빨아들이는 것 같아요 | anstiftung_2987, rcint_25666 |
| 흡입·공기 흐름 | `SUCTION_ABSENT` | 흡입 불가 | 먼지를 전혀 빨아들이지 못해요 | restart_11255 |
| 흡입·공기 흐름 | `AIR_PATH_BLOCKED` | 흡입 통로 막힘 | 흡입 통로에 뭔가 끼어 막혔어요 | anstiftung_2903, rcint_32729 |
| 먼지·필터 | `INLET_DUST_EXCESS` | 흡입구 먼지 과다 | 흡입구에 먼지가 많은 것 같아요 | 팀 요구 추가 |
| 먼지·필터 | `INTERNAL_DUST_ACCUMULATION` | 내부 먼지 축적 | 안에 먼지 뭉치가 많이 보여요 | anstiftung_2987 |
| 먼지·필터 | `FILTER_DIRTY` | 필터 오염 | 필터가 먼지로 많이 더러워요 | rcint_25666 |
| 먼지·필터 | `FILTER_BLOCKED` | 필터 막힘 | 필터가 막혀 있어요 | rcint_12432, restart_11613 |
| 소리·열·냄새 | `ABNORMAL_NOISE` | 이상 소음 | 평소와 다르게 큰 소리가 나요 | rcint_1080, anstiftung_2987 |
| 소리·열·냄새 | `OVERHEATING` | 과열 | 사용하면 너무 뜨거워져요 | restart_16305 |
| 소리·열·냄새 | `BURNING_SMELL` | 타는 냄새 | 타는 냄새가 나요 | rcint_12772 |
| 소리·열·냄새 | `SPARKS_VISIBLE` | 불꽃 발생 | 전원 버튼 쪽에서 불꽃이 보여요 | rcint_13350 |
| 브러시·바퀴 | `BRUSH_NOT_ROTATING` | 브러시 회전 불가 | 밑에 있는 청소 브러시가 안 돌아요 | restart_10620, fixitclinic_742 |
| 브러시·바퀴 | `BRUSH_HAIR_ACCUMULATION` | 브러시 축 털 축적 | 브러시 축 끝에 머리카락이 잔뜩 쌓였어요 | rcint_32214 |
| 브러시·바퀴 | `DRIVE_BELT_DETACHED` | 구동 벨트 이탈 | 벨트가 모터 축에서 빠져 있어요 | rcint_32214 |
| 브러시·바퀴 | `WHEEL_STUCK` | 바퀴 고착 | 바퀴가 걸려서 안 움직여요 | rcint_15674 |
| 브러시·바퀴 | `WHEEL_DETACHED` | 바퀴 이탈 | 바퀴가 빠졌어요 | rcint_25297, restart_19058 |
| 센서·오류 표시 | `SENSOR_DIRTY` | 센서 오염 | 센서 표면이 더러워 보여요 | anstiftung_6772, rcint_21434 |
| 센서·오류 표시 | `FALSE_OBSTACLE_DETECTION` | 장애물 오인식 | 앞에 아무것도 없는데 장애물이 있다고 해요 | anstiftung_6772 |
| 센서·오류 표시 | `ERROR_DISPLAYED` | 오류 표시 | F2 오류가 떠요 | rcint_21434, rcint_27354 |
| 스위치·배선·기판 | `SWITCH_UNRESPONSIVE` | 스위치 동작 불가 | 시작 버튼을 눌러도 작동하지 않아요 | rcint_22998 |
| 스위치·배선·기판 | `WIRE_BROKEN` | 배선 단선 | 전선이 끊어져 있어요 | rcint_10275, anstiftung_2774 |
| 스위치·배선·기판 | `CONNECTOR_LOOSE` | 커넥터 연결 이탈 | 내부 케이블 연결이 빠져 있어요 | anstiftung_5511 |
| 스위치·배선·기판 | `SOLDER_JOINT_LOOSE` | 납땜 접합 불량 | 기판 납땜 연결이 떨어져 있어요 | rcint_19834, rcint_25741 |
| 스위치·배선·기판 | `PCB_COMPONENT_FAULT_REPORTED` | 기판 부품 이상 보고 | 점검 결과 속도 제어 기판의 부품에 이상이 있어요 | rcint_19745 |
| 모터 | `MOTOR_NOT_ROTATING` | 모터 회전 불가 | 모터가 돌지 않아요 | anstiftung_4182 |
| 모터 | `MOTOR_BRUSH_CONTACT_POOR` | 모터 카본 브러시 접촉 불량 | 점검해 보니 카본 브러시 접촉이 좋지 않아요 | rcint_23473 |
| 수분·부식 | `LIQUID_INGRESS` | 물 유입 | 청소기가 물을 빨아들였어요 | anstiftung_6768 |
| 수분·부식 | `CORROSION_VISIBLE` | 부식 흔적 | 모터 쪽에 녹이 보여요 | rcint_21043 |
| 외형·부속품 | `HOUSING_BROKEN` | 덮개·외장 파손 | 덮개가 깨져 있어요 | anstiftung_4980 |
| 외형·부속품 | `HOUSING_DENT` | 외장 찌그러짐 | 본체 한쪽이 찌그러져 있어요 | 팀 요구 추가 |
| 외형·부속품 | `HOUSING_CRACK` | 외장 잔금·균열 | 외장 표면에 가는 금이 보여요 | 팀 요구 추가 |
| 외형·부속품 | `HOSE_BROKEN` | 호스 파손 | 호스 연결 부위가 찢어졌어요 | rcint_20795, restart_18657 |
| 외형·부속품 | `CORD_REWIND_FAILURE` | 전원선 되감기 불가 | 전원선이 다시 들어가지 않아요 | restart_8496 |
| 외형·부속품 | `DUSTBIN_OPEN_FAILURE` | 먼지통 열림 불가 | 먼지통이 안 열려요 | rcint_22042 |
| 외형·부속품 | `SEAL_LEAKAGE_REPORTED` | 밀폐 불량 보고 | 점검 결과 밀폐가 잘 안 되는 것 같아요 | rcint_23225 |
| 외형·부속품 | `DUST_LEAKAGE` | 먼지 외부 배출 | 청소할 때 먼지가 방 안으로 다시 나와요 | rcint_23225 |

## 원본 분류별 건수

이 값은 데이터셋의 사후 고장 분류입니다. 신규 소견이나 사진 모델의 클래스가 아닙니다.

| 원본 분류 | 건수 |
|---|---:|
| Cable/cord | 568 |
| Motor | 393 |
| Power/battery | 361 |
| Internal damage | 309 |
| Blockage | 297 |
| Button/switch | 240 |
| Filter | 123 |
| External damage | 80 |
| Overheating | 70 |
| Hose/tube/pipe | 70 |
| Brush | 41 |
| Wheels/rollers | 39 |
| Dustbag/canister | 39 |
| Other | 37 |
| Liquid damage | 23 |
| Accessories/attachments | 13 |
| Display/LED | 8 |

원본: [Open Repair Alliance DustUp](https://github.com/openrepair/data/blob/main/quests/vacuums/dustup.csv), CC BY-SA 4.0. 세부 근거 원문과 제공자는 data/observation_vocabulary.json에 보존했습니다. 한국어 용어·예문은 AI 보조 작성 초안입니다.

입력 및 출력 규칙은 observation_normalization.md를 참고하세요. 목록은 모델 학습용 정답 데이터나 작동 중인 MCP 서버가 아닙니다.
