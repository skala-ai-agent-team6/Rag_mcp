# PCB 표면 결함 라벨 참고

문서 종류: technical_reference_summary / 검색 컬렉션: pcb_documents

출처: Huang, Wei, Zhang, Liu, “HRIPCB: a challenging dataset for PCB defects detection and classification” (2020).
[논문](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/joe.2019.1183)

논문에 소개된 표면 결함 분류는 missing hole, mouse bite, open circuit, short, spur, spurious copper이다. 결함 위치는 바운딩 박스로 표시한다. 논문 데이터는 이미지 편집으로 결함을 만든 데이터셋이며 실제 제품의 수리 결과 데이터는 아니다.

아래 여섯 라벨은 사용자가 전달한 팀 모델의 전체 클래스 목록과 일치한다. 실제 학습 데이터가 위 논문 데이터셋인지는 확인되지 않았다. 라벨 정의와 별칭은 data/pcb_label_taxonomy.json에 기록한다.

| 팀 모델 라벨 | 검색용 한국어 설명 |
|---|---|
| mouse_bite | 도체 패턴 가장자리의 일부가 파인 형태의 결손 |
| open_circuit | 도체 패턴이 끊어진 형태 |
| short | 분리되어야 하는 도체 패턴 사이의 연결 |
| spur | 도체 가장자리에서 튀어나온 부분 |
| spurious_copper | 불필요하게 남아 있는 구리 조각 |
| missing_hole | 있어야 하는 홀의 누락 |

RAG는 팀원이 전달한 라벨 문자열을 받는다. hole missing은 missing_hole로 통일한다. 숫자 class_id가 나중에 전달된다면 모델의 실제 매핑표가 필요하며, 이 표의 행 순서를 ID로 사용하지 않는다.

적용 범위: 표면 결함 후보 설명. 특정 회로 기능, 배터리 이상, 모터 고장과의 인과관계는 추가 증거가 필요하다. mouse_bite 검출을 곧바로 전기적 단선 확정으로 바꾸지 않는다.

review_status: pending_team_review. 원문 전체·이미지는 포함하지 않은 출처 기반 요약이다.
