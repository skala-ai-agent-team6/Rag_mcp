# 한 줄 소견과 PCB 결함 이름을 RAG와 연결하기

팀 합의 반영: PCB 담당자는 결함 이름을 텍스트로 보낸다. 전체 클래스는 missing_hole, mouse_bite, open_circuit, short, spur, spurious_copper로 확정되었다. 접수 시에는 기사의 한 줄 소견을 받는다. 소견은 사진 분석 AI가 초안으로 작성할 수도 있다. API 필드명은 이후 합의한다.

라벨 정의는 data/pcb_label_taxonomy.json에서 정확히 매칭한다. hole missing 같은 표현은 명시된 별칭으로만 변환한다. 미등록 라벨을 가장 비슷한 정상 라벨로 강제 변경하지 않는다. 여러 결함이 있으면 목록으로 보존한다. 각 라벨의 정의 문서는 data/pcb_documents/labels/ 아래에 별도로 있다. 정의 검색은 정확 일치로 처리하고, 관련 기술 설명은 문서 검색으로 보완한다.

## 검색 흐름

한 줄 소견 → 수리 사례 검색.

PCB 결함 이름이 함께 있으면 → 별도로 PCB 기술 문서 검색 + 수리 사례 검색의 추가 단서.

“흡입구에 먼지가 많아보입니다”는 관찰이다. 이 문장만으로 먼지가 고장 원인이라고 확정하지 않는다. PCB 분석 결과가 아직 없어도 사례 검색을 진행한다. 먼지·막힘·소음·전원·센서·모터·배선 등을 폭넓게 포함하며 PCB/MOTOR/SW를 최초 필수 필터로 제한하지 않는다. PCB 문서는 pcb_documents에 별도 보관한다.

## 입력 초안

examples/intake_observation.json에 한 줄 소견 예시가 있다. AI가 자동 작성했다면 observation.origin을 ai_image로 기록하고 실제 기사 확인 전에는 technician_confirmed를 false로 둔다. AI 초안을 실제 원인 확정으로 저장하지 않는다. 팀의 AI 작성 내용 승인 규칙에 맞춰 기사 확인 여부를 관리한다.

PCB 라벨 배열이 빈 것과 분석 후 검출 없음은 다르므로 not_provided, no_detections, completed, failed 같은 상태를 합의한다. 라벨만 전달받은 경우 점수·좌표를 임의로 채우지 않는다. 결과 이미지나 OCR은 현재 RAG 입력의 필수 항목이 아니다.

## 검색 결과 사용

유사 사례의 증상, 조치, 원본 수리 결과, 출처를 함께 반환한다. Fixed는 원본에서 성공으로 기록된 경우이며 Repairable은 수리 완료가 아니다. End of life와 Unknown도 원래 의미로 남긴다. 실패 사례는 실패 또는 제약의 근거로 제시한다.

DustUp은 여러 언어로 기록되어 있다. 한국어 소견으로 검색할 때는 다국어 임베딩을 사용하고 실제 질문으로 교차 언어 검색 품질을 확인하거나 출처를 유지한 번역본을 준비한다. 현재 임베딩·검색은 실행하지 않았다.

이전 examples/pcb_observation.json은 스크린샷 라벨을 수기로 기록한 참고 예시이며 현재 팀 API 형식이 아니다.
