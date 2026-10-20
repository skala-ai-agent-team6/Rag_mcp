# 결함 라벨별 점검·조치 가이드 v0.1

PCB 6종 + 찌그러짐 6종, 총 12개 문서다. 파손(damage) 6종과 dent의 bonnet·rear-bumper는 이번 작성 범위에서 제외했다.

## 파일

- `guidance.jsonl`: 12개 구조화 레코드. `text`는 RAG용 본문이다.
- `pcb/*.md`, `dent/*.md`: 사람이 검토할 수 있는 라벨별 본문.
- `policy.json`: 공통 심각도·승인·적용 정책과 참고 출처.

RAG MCP의 `retrieve_repair_context`가 이 폴더의 지침을 정확한 라벨로 조회하여 사례와 함께 반환한다. 지침은 dense 색인에 넣지 않는다. 모델 라벨 지원 범위와 기존 외형 정의도 dent 6종으로 맞췄다. 초안의 검토·적용 대기 상태는 유지한다.

## 사용 전 알아둘 점

이 자료는 실제 사례를 꾸민 것이 아니라 팀이 검토할 **점검·조치 지식 문서**다. `confirmed_fault`, `repair_outcome`은 모두 null이다. L1/L2/L3는 팀 제안 단계이며 제조사·IPC 등급이 아니다. 입력이 라벨뿐이면 **U(판단 보류)**가 기본값이다.

PCB의 L1 조건에 ‘오인식이면 후보 정정’이 있는 경우는 확인된 결함을 경미하다고 승인한다는 뜻이 아니다.

찌그러짐 6종은 **자동차 부위 기준 초안**이다. 사용자가 청소기 대응표를 추후 제공할 예정이므로 `target_component`는 null, `applicability_status`는 `awaiting_vacuum_mapping`이다. 대응표를 받으면 부품 이름과 함께 재질·기능·내부 간섭·고정·점검·조치를 수정해야 한다. 앞범퍼라는 이름이 비슷해도 차량과 청소기 조치를 그대로 공유하지 않는다.

## 문서 목록

| 분류 | 라벨 | 문서 |
|---|---|---|
| pcb | `missing_hole` | [missing_hole — 구멍 누락](pcb/missing_hole.md) |
| pcb | `mouse_bite` | [mouse_bite — 도체 가장자리 결손](pcb/mouse_bite.md) |
| pcb | `open_circuit` | [open_circuit — 회로 끊김](pcb/open_circuit.md) |
| pcb | `short` | [short — 단락 후보](pcb/short.md) |
| pcb | `spur` | [spur — 도체 돌기](pcb/spur.md) |
| pcb | `spurious_copper` | [spurious_copper — 불필요한 구리](pcb/spurious_copper.md) |
| dent | `boot` | [boot — 트렁크 부위 찌그러짐](dent/boot.md) |
| dent | `doorouter` | [doorouter — 도어 외판 찌그러짐](dent/doorouter.md) |
| dent | `fender` | [fender — 펜더 찌그러짐](dent/fender.md) |
| dent | `front-bumper` | [front-bumper — 앞범퍼 찌그러짐](dent/front-bumper.md) |
| dent | `quaterpanel` | [quaterpanel — 쿼터 패널 찌그러짐](dent/quaterpanel.md) |
| dent | `roof` | [roof — 지붕 패널 찌그러짐](dent/roof.md) |

## 검색 연결 권장 방식

1. 모델의 정확한 라벨은 `(category, label)`로 해당 가이드를 우선 조회한다. `quaterpanel`은 원래 철자를 유지하고 `quarterpanel`을 별칭으로 받는다.
2. 기사 소견과 추가 측정·기능 정보를 사용해 관련 문서를 보조 검색한다. 라벨이 같은 문서를 찾는 작업 전체를 dense 유사도에 맡기지 않는다.
3. 반환 결과에 적용 범위·검토 상태·문서 ID를 포함한다. 청소기 대응 대기 중인 dent 문서는 실제 청소기 조치 생성에서 제외한다.
4. 공통 정책을 항상 함께 제공한다. 문서를 분할하면 각 청크에 라벨, 범위, 조건부 지침이라는 표시를 유지한다.
5. `confirmed_fault`를 채우거나 상태를 확정하는 작업은 별도의 담당자 확인·승인을 거친다.

### 라벨만 전달된 경우의 답변 예시

입력: `mouse_bite`

> 도체 가장자리 결손 후보입니다. 현재 라벨만으로는 심각도를 판단할 수 없습니다(U). 패턴의 연결 상태와 남은 폭을 정상 도면·규격과 비교해야 합니다. 확대 사진과 관련 기능 증상을 확인해 주세요. 복구·교체 여부는 점검 결과와 담당자 승인 후 결정합니다.

이 예시는 실제 수리 이력이 아닌 응답 형식 예시다.

## 검토 체크

- 라벨 12개가 팀 모델의 실제 출력 문자열과 일치하는지 확인.
- 청소기 부위 대응표와 점검 방법을 반영한 뒤 외형 문서의 적용 상태 갱신.
- 제품별 수치·회로·허용 재작업 기준은 실제 매뉴얼이 있을 때 추가.
- 팀 검토 완료 후 검토자·버전 기록 및 색인 반영.

## 참고 범위

- [HRIPCB 논문](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/joe.2019.1183): PCB 클래스·합성 이미지라는 배경만 참고. 심각도·행동 규칙은 논문의 기준이 아니다.
- [Tesla 재질별 작업 지침](https://service.tesla.com/docs/BodyRepair/Body_Repair_Procedures/Model_3/HTML/en-us/GUID-B4A61C9E-4CE2-4D9A-B9B3-B6D74EEFE038.html): 재질·부품별 수리 제한을 확인한다는 원칙만 참고.
- [Tesla 앞범퍼 지침](https://service.tesla.com/docs/BodyRepair/Body_Repair_Procedures/Model_3_2024/HTML/en-us/GUID-68C87AAD-73AC-48DA-B4A4-A95499CF5A0A.html): 장착 센서와 수리 위치 확인의 배경만 참고.

본문은 자체 작성한 일반 점검 제안이다. 위 링크들이 각 조건·조치를 승인하거나 모든 차종·청소기에 적용할 수 있다고 보증하는 것은 아니다.
