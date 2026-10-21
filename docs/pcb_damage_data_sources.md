# PCB·외형 손상 RAG 자료 조사

확인일: 2026-10-20

구조화 파일: `data/research/pcb_damage_candidates_2026-10-20.jsonl`

## 이번에 확보한 범위

공개 자료 7건을 직접 확인하고 짧은 한국어 요약과 출처를 기록했다.

- 전문 PCB 수리업체의 사례 2건
- 일반 PCB 기술 안내 1건
- 청소기 제조사 점검 안내 1건
- 청소기 커뮤니티 수리 가이드 1건
- 청소기 소유자의 단기 수리 성공 보고 1건
- 결과가 확인되지 않은 청소기 진단 질문 1건

이는 **수리 완료가 검증된 사례 7건**을 뜻하지 않는다. 원문 전체나 이미지를 복제한 데이터셋도 아니다. 현재 검색 코드의 로딩 대상에 추가하지 않았으며, 임베딩·벡터 DB 반영은 아직 하지 않았다.

## 출처

| ID 끝부분 | 자료 | 용도 |
|---|---|---|
| ctc-missing-via | [Circuit Technology Center: Method for Adding A Via Hole](https://www.circuitrework.com/blogs/10050.html) | 비아 연결 복구 참고 |
| ctc-hidden-short | [Circuit Technology Center: X-Ray Finds Shorts in Drilled Holes](https://www.circuitrework.com/blogs/10010.html) | 내부 단락 점검 참고 |
| ctc-conductor-repair | [Circuit Technology Center: Conductor Repair](https://www.circuitrework.com/blogs/10015.html) | 손상 패턴 복구 참고 |
| eufy-ir-pin | [eufy: 재조립 후 충전대 복귀 실패](https://service.eufy.com/article-description/Why-does-my-RoboVac-fail-to-return-to-the-charging-base-after-I-disassembled-and-reassembled-the-RoboVac) | 핀 변형과 센서 연결 점검 |
| roomba890-bumper | [iFixit: Roomba 890 Bumper Sensors Replacement](https://www.ifixit.com/Guide/iRobot+Roomba+890+Bumper+Sensors+Replacement/149777) | 범퍼·센서·휠 원인 후보 구분 |
| roomba-s9-spring | [Robot Reviews: s9 Bumper Sensor’s Error 9 Fix](https://www.robotreviews.com/chat/viewtopic.php?t=22626) | 특정 작성자의 범퍼 복귀 불량 사례 |
| roomba650-wheel-board | [iFixit: Roomba 650 Error 5](https://www.ifixit.com/Answers/View/196744/Resistance+in+right+wheel-%22error+5%22) | 휠 문제와 보드 문제의 감별 참고 |

## 현재 프로젝트에서의 사용 방향

1. PCB 일반 문서는 `pcb_documents`의 기술 근거로 검색한다. 제품 모델이 불명확한 일반 PCB 사례를 청소기 확정 수리 이력으로 표시하지 않는다.
2. 청소기 범퍼·커넥터 자료는 제품 모델과 증상을 포함해 외형/기계/연결부 점검 근거로 검색한다.
3. 실제 수리 보고에는 `outcome_status`를 유지한다. 작성자 보고, 업체 보고, 미확정 질문을 구분해 답변에 표시한다.
4. `related_pcb_labels`는 검색 힌트다. 원문에 사진 모델의 검출 결과가 있었다는 뜻이 아니다. 모델의 감지 결과를 확정 원인으로 승격하지 않는다.
5. 기사 소견·PCB 라벨·외형 라벨을 각각 보존하고 검색 근거를 연결한다. 청소기 증상이 같은 자료를 우선하고 일반 PCB 문서는 보조 근거로 제시한다.

## 아직 부족한 부분

- 이번 자료에는 **청소기 외장 찌그러짐과 실제 수리 결과가 함께 확인된 사례가 없다.**
- 범퍼 걸림, 스프링 복귀 불량, 핀 휨은 각각 다른 관찰이다. 이를 모두 `dent` 확정 사례로 변환하지 않는다.
- `mouse_bite`, `spur`, `spurious_copper`의 실제 수리 결과 자료는 이번 목록으로 충족되지 않는다.
- 외형 모델의 현재 여섯 라벨은 부품명이 아니라 표면 결함 종류다. `bonnet`, `Headlight` 등 기존 부위 라벨은 지원하지 않는다. 표면 결함 라벨만으로 실제 손상 위치·재질·청소기 모델 적용성을 입증하지 않는다.
- Circuit Technology Center는 저작권 유보를 표시한다. 모든 출처의 원문 대량 수집·재배포·상용 이용 조건은 검증하지 않았다. 파일의 `license_status`는 사용 허가를 의미하지 않는다.

## 데이터 필드

- `observations_ko`: 출처에서 확인한 증상·관찰의 짧은 요약
- `action_ko`: 실제 보고된 조치 또는 가이드의 점검 안내
- `outcome_ko`: 출처가 보고한 결과. 없으면 null
- `outcome_status`: 업체 보고 / 사용자 단기 보고 / 미확정 / 사례 아님
- `source_type`, `source_url`, `source_locator`: 자료 종류와 원문 확인 위치
- `product_domain`, `model`, `applicability_ko`: 적용 범위
- `retrieval_hints`: 한국어·영어 검색 보조어
- `literal_housing_dent_evidence`: 외장 찌그러짐이 원문에서 확인됐는지 여부
- `review_status`: 현재는 모두 candidate
