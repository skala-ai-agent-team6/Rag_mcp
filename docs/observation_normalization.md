# 자연어 소견 정규화 도구 초안

담당 기능: 원문에서 관찰·증상 표현을 추출해 data/observation_vocabulary.json의 code/label_ko로 바꾼다. 진단 원인, 조치, 수리 결과를 생성하는 기능은 아니다. 이 파일은 명세 초안이며 MCP 서버·LLM 호출은 구현하지 않았다.

도구 이름 제안: normalize_observations

## 보존 규칙

- 원문을 raw_text로 보존한다. 표준어만 보내면 어감·장소·시간·코드·희귀 표현이 사라질 수 있으므로 RAG에도 원문을 함께 전달한다.
- 하나의 문장에서 여러 관찰을 반환한다. 서로 배타적인 단일 분류로 만들지 않는다.
- polarity: present / absent. “막히지 않았다”는 absent로 남긴다.
- certainty: reported / suspected. “같다”, “의심된다”, “보인다” 등은 suspected로 남긴다. reported는 발화자가 그렇게 보고했다는 의미이며 기기 점검으로 확정했다는 의미가 아니다.
- evidence_text는 raw_text의 실제 부분 문자열이어야 한다. 빈 문자열을 허용하지 않는다.
- 입력에 없는 위치나 부품명을 보충하지 않는다. “먼지가 많다”에 흡입구라는 위치가 없으면 미분류 구절로 남기거나 넓은 용어를 별도로 검토한다.
- 원문에 시간·위치·오류 코드가 있으면 별도 context/evidence 또는 원문으로 보존한다. F2 등의 코드를 새로 만들지 않는다.
- 먼지가 보인다는 말에서 막힘·흡입력 저하·모터 고장을 자동 추가하지 않는다. 스위치가 반응하지 않는다고 스위치 부품 고장을 확정하지 않는다.
- “배터리 정상”을 “배터리 빠른 방전”의 부정으로 변환하지 않는다. 정상 보고는 정상 보고로만 남긴다.
- “고장 아닌가요?”는 질문이므로 확정 보고로 취급하지 않는다. 상반된 보고는 출처별로 보존한다.
- 맞는 코드가 없으면 unmapped_fragments에 넣고 원문으로 검색한다. 가장 비슷한 코드로 강제 변환하지 않는다.
- PCB/외형 모델 출력은 별도의 출처로 받는다. 자연어 소견에서 PCB six-class 라벨을 추측해 채우지 않는다.
- origin은 technician / ai_image 등으로 명시한다. AI 초안을 기사가 확인했다면 technician_confirmed=true를 별도로 기록한다. 자연어 변환이 끝났다고 자동으로 true로 바꾸지 않는다.

## 예시

입력: “흡입구에 먼지가 많은 것 같아요. 필터는 막히지 않았어요.”

```json
{
  "raw_text": "흡입구에 먼지가 많은 것 같아요. 필터는 막히지 않았어요.",
  "origin": "technician",
  "observations": [
    {
      "code": "INLET_DUST_EXCESS",
      "label_ko": "흡입구 먼지 과다",
      "polarity": "present",
      "certainty": "suspected",
      "evidence_text": "흡입구에 먼지가 많은 것 같아요"
    },
    {
      "code": "FILTER_BLOCKED",
      "label_ko": "필터 막힘",
      "polarity": "absent",
      "certainty": "reported",
      "evidence_text": "필터는 막히지 않았어요"
    }
  ],
  "unmapped_fragments": []
}
```

## RAG와 결합

원문 + 정규화 관찰 + PCB 검출 이름 + 외형 모델의 원본 결과를 LangGraph에서 묶어 사례 검색에 전달한다. 소견을 검색 도구가 중복 정규화하지 않도록 역할을 합의한다. 외형 모델의 실제 클래스 목록은 아직 확인되지 않았으므로 새 클래스명을 정해 모델 출력처럼 취급하지 않는다.

검색어에는 관찰의 부정·추측을 문장으로 표시한다. 예: “흡입구 먼지 과다 의심. 필터 막힘은 없다고 보고됨.” 그러나 임베딩이 부정을 항상 정확히 처리한다고 가정하지 않는다. 관련 사례를 넓게 찾은 뒤 실제 관찰과 모순되는지 재정렬/검토하고, 정상 관찰은 제외 필터보다 비교 근거로 활용한다.

DustUp 본문은 다국어이고 정규화 용어가 아직 모든 사례에 태깅되어 있지 않다. 그러므로 이 code를 데이터베이스 필수 필터로 걸면 안 된다. 처음에는 원문·표준 용어를 함께 검색에 사용하고, 사례에도 동일한 체계로 관찰을 추출할 경우 검증 후 메타데이터를 추가한다. 수리 후 조치와 수리 전 증상을 혼동하지 않는다.

## 이후 구현 검증 예시

- “흡입구에 먼지가 많아 보여요” → INLET_DUST_EXCESS/present/suspected만 반환. AIR_PATH_BLOCKED를 추가하지 않음.
- “필터가 막힌 건 아닙니다” → FILTER_BLOCKED/absent/reported.
- “전원이 안 켜지고 타는 냄새가 나요” → POWER_NO_START + BURNING_SMELL.
- “배터리는 정상인데 켜졌다가 멈춰요” → BATTERY_NORMAL + STOP_AFTER_START.
- “필터는 안 막힌 것 같아요” → FILTER_BLOCKED/absent/suspected.
- “먼지가 많아요” → 위치를 추측하지 않고 unmapped_fragments에 보존.
- 처음 보는 현상 → 미분류와 원문을 반환. 임의의 기존 코드로 분류하지 않음.

이 예시는 요구 동작이며 현재 구현의 테스트 통과 결과가 아니다.
