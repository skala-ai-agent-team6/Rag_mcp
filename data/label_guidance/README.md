# 결함 라벨별 점검 지침 v0.3

PCB 6종과 외형 표면 결함 6종, 총 12개 팀 작성 초안이다. 제조사 승인 수리 절차나 실제 수리 사례가 아니다.

## 파일

- `guidance.jsonl`: RAG MCP가 정확한 라벨로 조회하는 구조화 지침 12개.
- `pcb/*.md`, `surface/*.md`: 담당자가 읽고 검토할 수 있는 같은 지침의 본문.
- `policy.json`: 공통 승인·적용 제한 정책.
- 외형 검색용 라벨 정의: `../damage_documents/labels.json`.

## 외형 모델 라벨

| 라벨 | 뜻 | 지침 |
|---|---|---|
| `crazing` | 잔금 | [crazing](surface/crazing.md) |
| `inclusion` | 이물 박힘 | [inclusion](surface/inclusion.md) |
| `patches` | 얼룩·녹 후보 | [patches](surface/patches.md) |
| `pitted_surface` | 패임 | [pitted_surface](surface/pitted_surface.md) |
| `rolled-in_scale` | 압연 스케일 후보 | [rolled-in_scale](surface/rolled-in_scale.md) |
| `scratches` | 긁힘 | [scratches](surface/scratches.md) |

외형 모델이 보내는 것은 결함 **종류**다. 위치 좌표는 현재 MCP에서 처리하지 않는다. 라벨만으로 실제 부품·재질·깊이·범위·심각도를 정하지 않는다. 특히 `rolled-in_scale`은 금속 압연 표면 용어이므로 청소기 부품 재질을 먼저 확인한다.

## PCB 모델 라벨

| 라벨 | 지침 |
|---|---|
| `missing_hole` | [구멍 누락](pcb/missing_hole.md) |
| `mouse_bite` | [가장자리 결손](pcb/mouse_bite.md) |
| `open_circuit` | [회로 끊김](pcb/open_circuit.md) |
| `short` | [단락 후보](pcb/short.md) |
| `spur` | [도체 돌기](pcb/spur.md) |
| `spurious_copper` | [불필요한 구리](pcb/spurious_copper.md) |

## 사용 원칙

라벨 지침은 `(category, label)`로 정확히 찾는다. 임베딩 점수로 다른 라벨의 지침을 대신하지 않는다. 외형·PCB 지침은 모두 **검토용 제안**이다. 응답에는 입력 기준 증상 판정과 점검 순서를 담고, 심각도 등급과 추가 질문은 제외한다. 실제 수리·교체·발주·확정 기록은 담당자 확인과 승인 후 진행한다.

표면 결함 지침은 사진에서 실제 위치·재질을 확인하는 질문과 조건부 점검을 반환한다. 모델 라벨이나 사례 검색 점수만으로 수리 원인을 확정하지 않는다.
