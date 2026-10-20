# 수리 진단 RAG · MCP

청소기 전용 서비스로, 기사 소견과 팀 모델의 라벨을 받아 과거 수리 사례·기술 문서를 검색한다. 요청에 `product_domain`을 넣지 않는다. 모델 추론은 팀원이 담당하고, 이 저장소는 결과 해석과 검색을 담당한다.

**소견 변환에는 프로젝트 `.env`의 `OPENAI_API_KEY`가 필요하다. 기본 모델: `gpt-4.1-mini`.**

**실행 방법과 팀 연동:** [MCP 사용 안내](docs/mcp_usage.md) · [실제 검색 실험](experiments/results/summary.md)

## 구성

```text
repair_rag_data/
  data/raw/dustup.csv             공개 원본 CSV 스냅샷
  data/repair_cases/all_cases.jsonl 전체 원본에서 기본 품질 필터를 거친 검색 후보
  data/repair_cases/excluded.json 제외된 원본 ID와 이유
  data/repair_cases/cases.jsonl   한국어 정리 예시 30건 (전체 후보에 포함)
  data/repair_cases/review.md     원문과 한국어를 함께 읽는 검토용 문서
  data/pcb_label_taxonomy.json   확정된 팀 모델 6개 라벨·별칭·한국어 설명
  data/observation_vocabulary.json 소견 표준 용어 초안·원본 근거·분류 건수
  data/pcb_documents/            PCB 기술 참고문서 3개
  data/pcb_documents/labels/     팀 제공 결함 정의 6개 (각 라벨 1문서)
  data/source_manifest.json      원본 해시·건수·출처
  examples/pcb_observation.json  사용자 이미지에서 보이는 라벨·점수 예시
  examples/intake_observation.json 기사 한 줄 소견 입력 예시
  docs/pcb_result_handoff.md     한 줄 소견·PCB 결함 이름과 RAG 연결 초안
  docs/observation_vocabulary.md 소견 표준 값 목록
  docs/observation_normalization.md 자연어 변환 도구 입력·출력 규칙
  build_dataset.py               원본으로부터 사례 문서 재생성
  build_observation_vocabulary.py 사례 근거와 소견 용어 목록 재생성
```

## 준비된 자료와 범위

수리 사례 검색 범위를 Open Repair Alliance DustUp 원본 전체 3,165건으로 넓혔다. all_cases.jsonl은 Poor data 및 빈 본문만 제외한 검색 후보이며, 나머지 모든 기록의 품질이 검증되었다는 의미는 아니다. 성공 외에 수리 가능·수명 종료·결과 미상도 원래 상태로 보존한다. 정확한 후보 건수와 상태 분포는 source_manifest.json에 기록한다.

기존 30건은 한국어 추출·검토 예시로 유지한다. all_cases.jsonl에도 같은 ID가 포함되므로 두 파일을 합쳐 중복 색인하지 않는다. 원본 전체에는 여러 언어와 짧은 기록이 섞여 있다. 기본 필터 이후 검색 평가로 제외 기준을 다듬는다.

`source_fault_type`은 원문을 사후 분류한 값이다. 우리 팀이 실제 기기를 확인한 확정 원인이라는 뜻은 아니다. 한국어 요약은 AI 보조 작성이고 `review_status=pending_team_review`이다. 조치만 기록된 사례에서 원인을 추측해 채우지 않았다. 원문에 없는 모델명, 측정값, 사진, YOLO 결과는 넣지 않았다.

PCB 기술 문서는 분류 용어 참고 1개와 Repair Wiki 기술 가이드 요약 2개다. 제조사 공식 서비스 매뉴얼은 아니다. 제품별 가이드의 회로·부품을 다른 제품에 직접 적용하지 않는다. 아직 삼성 로봇청소기의 특정 결함과 특정 PCB 검출 라벨을 실증적으로 연결한 자료는 없다.

팀이 확정한 결함 라벨 6종을 별도 정의 문서로 추가했다. 라벨 정의의 출처는 사용자가 전달한 팀 목록이다. 이는 수리 지침이나 전기적 측정 결과가 아니다. 라벨을 정확히 찾아 설명하고, 한 줄 소견과 함께 과거 사례 검색의 단서로 사용한다.

자연어 소견을 정해진 값으로 변환할 때 사용할 용어 초안을 추가했다. 40개는 원문 사례를 근거로 작성했고, 흡입구 먼지 과다·외장 찌그러짐 2개는 팀 요구로 추가했다. 빈도 표는 원본 17개 고장 분류의 건수이며 새 용어별 빈도가 아니다. 현재 이 용어를 사용하는 OpenAI 기반 소견 정규화 MCP가 구현되어 있다. 사례 전체에 용어가 태깅되어 있는 것은 아니다.

## 원본과 이용 표시

- DustUp: [CSV](https://github.com/openrepair/data/blob/main/quests/vacuums/dustup.csv), [설명](https://openrepair.org/open-data/insights/vacuum-cleaners/), [메타데이터](https://github.com/openrepair/data/blob/master/quests/vacuums/tableschema.json). Open Repair Alliance 및 각 record의 data_provider에 귀속. CC BY-SA 4.0. 변경: 30건 선정, 한국어 요약, 필드 구조화. 원본 CSV 자체는 수정하지 않음.
- Repair Wiki: 각 문서 안의 원본 링크와 기여자 출처 유지. 기본 CC BY-SA 3.0, 별도 표시 우선. 변경: 한국어 요약 및 적용 범위 설명.
- HRIPCB 논문: 저자와 DOI를 표시한 짧은 요약. 논문 전체나 이미지를 복제하지 않음.
- 공개 기록을 사내 기사 접수·수리 이력으로 위장하지 않는다. `source_type`과 원본 ID를 검색 결과에도 전달한다.

## SQL 스키마와의 관계

현재 회사 SQL의 repair_case / repair_report / confirmed_fault는 회사가 실제로 관리하는 건에 사용한다. 외부 공개 기록에는 필수 product_id, center_id, technician_id가 없으므로 가짜 외래키를 만들어 집어넣지 않는다.

이 준비본은 출처를 가진 외부 문서로 색인한다. 회사의 신규 수리 확정 건은 이후 별도 export를 통해 같은 repair_cases 컬렉션에 넣을 수 있다. external_community_repair_record와 internal_confirmed_repair를 구분한다.

## 구현과 검증

- `observation-mcp`: OpenAI가 기사 한 줄 소견의 문맥을 읽어 42개 표준 소견 중 후보 선택. 원문·부정·추정·미등록 구절 보존.
- `pcb-mcp`: 팀 모델의 6개 결함 라벨과 별칭 해석. 이미지 추론은 하지 않음.
- `damage-mcp`: dent 6개 라벨 해석. 자동차 부위라는 출처·적용 범위 보존.
- `rag-mcp`: 원문 소견 + PCB + 적용 가능한 외형 라벨로 다국어 dense 검색. 사례·PCB 참고·라벨 정의를 분리 반환.
- 2,711개 사례 / PCB 문서 9개 / 외형 라벨 문서 6개를 별도 Qdrant 컬렉션에 색인.
- `tests/`: 정규화·출처·부정·라벨 검증·MCP 프로토콜·색인 계약 테스트.
- `experiments/`: 실제 임베딩을 사용한 소견 단독/결합 검색 실험. 기존 results는 규칙 기반 버전의 기록이다. OpenAI 전환 후 실행은 results/openai에 별도 저장하며 아직 실측하지 않았다.

전체 후보의 search_text에는 원문 증상과 조치가 섞여 있다. 원본 정답 표현을 신규 질문에 그대로 넣어 검색 성능이 좋다고 평가하면 안 된다. 동일 모델의 확인된 내부 수리 사례가 아니며, 결과에 원본 상태·출처·모델 적용 미상을 표시한다.

재생성: `python3 build_dataset.py`, `python3 build_observation_vocabulary.py`. 데이터 원본은 유지되며 검색 색인은 `repair-mcp index`로 별도 생성한다. 코드 실행은 `docs/mcp_usage.md` 참조.

# 참고 서비스 가이드

- 모델: VR50T95735W/AA
- 자료: [SamsungParts 서비스 가이드](https://samsungparts.com/blogs/vacuum/vr50t95735w-aa)
- 범위: 분해·조립 및 부품 확인
- 확인 사항: 소프트웨어 오류 코드표는 포함되지 않음
