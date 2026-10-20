# MCP 실행 및 팀 연동

## 담당 범위

서비스는 청소기 전용이다. 요청에서 제품 종류를 선택하지 않으며 `product_domain` 입력 항목은 제거했다. 기존 요청에 이 항목이 있다면 삭제한다.

팀원이 실행한 모델의 **라벨 결과**를 받는다. 사진이나 모델 가중치를 받지 않는다.

| 서버 | 도구 | 입력 | 출력 |
|---|---|---|---|
| observation-mcp | normalize_observation | 한국어 기사 소견, 작성 주체, 기사 확인 여부 | OpenAI가 선택한 표준 소견 후보, 원문, 부정/추정, 미등록 구절 |
| pcb-mcp | interpret_pcb | PCB 라벨 문자열 배열 | 6종 표준 라벨, 설명, 미등록 라벨 |
| damage-mcp | interpret_damage | damage_type + part 배열 | 14종 부위/유형, 도메인 불일치 여부 |
| rag-mcp | retrieve_repair_context | 원문 소견 + PCB 라벨 + 외형 라벨 | 과거 사례, 라벨 정의, PCB 참고 문서, 출처와 점수 |
| rag-mcp | search_reference_documents | 검색어, 문서 컬렉션 | PCB 또는 외형 정의 문서 dense 검색 |

보조 목록 도구: `list_observation_terms`, `list_damage_labels`.

RAG에는 **원문과 원본 라벨**을 전달한다. RAG가 같은 정규화 함수를 내부에서 사용하므로 네 서버를 반드시 차례로 호출할 필요는 없다. 별도 해석 MCP는 화면의 해석 미리보기 또는 LangGraph가 해당 도구만 필요할 때 사용한다. 미리보기 결과에서 양성 코드만 추려 보내면 부정·추정·미등록 표현이 사라지므로 그렇게 전달하지 않는다.

```text
기사 소견 ─── observation-mcp (표준 소견 미리보기)
PCB 결과 ─── pcb-mcp         (라벨 해석 미리보기)
외형 결과 ── damage-mcp      (라벨 해석 미리보기)
     └── 원문 소견 + 원본 라벨 ── rag-mcp ── 출처가 있는 검색 근거
                                                  └── LangGraph 답변 생성
```

이 네 MCP는 업무 DB를 쓰지 않는다. Spring 접수 저장·작업 큐·SSE·추가 사진 interrupt/resume·사람 승인·발주·최종 원인 저장은 다른 담당 서비스와 연결한다. 이 구현에는 그 오케스트레이션 전체가 포함되지 않는다.

## 처음 실행

프로젝트 폴더에서 Python 3.11~3.13과 `uv`를 사용한다. 먼저 프로젝트 루트 `.env`에 키를 등록한다. 파일이 없다면 `.env.example`을 복사한다. `.env`는 Git에서 제외한다.

```dotenv
OPENAI_API_KEY=여기에_본인_API_키
OPENAI_OBSERVATION_MODEL=gpt-4.1-mini
```

키 설정 후 서버를 다시 시작한다. 소견 변환만 먼저 시험하려면 아래 명령을 실행한다. 이 호출에는 API 사용량이 발생한다.

```bash
uv sync --locked --python 3.11
uv run repair-mcp normalize "흡입구에 먼지가 많은 것 같아요. 필터는 막히지 않았어요."
```

전체 검색 실행:

```bash
uv sync --locked --python 3.11
uv run repair-mcp index
uv run pytest -q
uv run python examples/call_mcp.py
uv run python experiments/run.py
```

- 소견 변환에는 OpenAI API 키가 필요하다. 임베딩/벡터 색인은 기존 로컬 모델을 사용한다. 키를 등록하지 않아도 색인·PCB/외형 라벨 해석은 실행할 수 있다.
- 첫 색인 때 Hugging Face에서 `intfloat/multilingual-e5-small`을 다운로드한다.
- 기본 Qdrant는 `.runtime/qdrant`, 모델 캐시는 `.runtime/models`에 저장한다. 모두 Git 제외.
- `index`와 로컬 RAG 서버를 동시에 실행하면 안 된다. 로컬 Qdrant 폴더는 한 프로세스가 사용한다.
- `examples/call_mcp.py`는 네 서버에 실제 MCP 프로토콜로 호출하는 예시다. 기본은 같은 프로세스의 in-memory transport다.
- 기본 출력은 소견 키워드·모델 라벨·사례 원문 발췌·참고문서 제목이다. `--json`을 붙이면 중간 응답과 전체 문서·출처를 포함한 JSON을 출력한다. 출력 형식만 바꾸며 검색 순위나 관련성 판단은 변경하지 않는다.
- 다운로드 완료 후 `HF_HUB_OFFLINE=1` 환경변수를 설정하면 모델을 오프라인으로 로드한다.

## HTTP 서버 실행

아래 명령을 **각각 다른 터미널에서** 실행한다.

```bash
uv run repair-mcp serve observation --transport http --port 8011
uv run repair-mcp serve pcb --transport http --port 8012
uv run repair-mcp serve damage --transport http --port 8013
uv run repair-mcp serve rag --transport http --port 8014
```

엔드포인트는 각각 `http://127.0.0.1:8011/mcp` ~ `http://127.0.0.1:8014/mcp`이다. 일반 REST POST API가 아니라 Streamable HTTP MCP 프로토콜을 사용한다.

```bash
uv run python examples/call_mcp.py --http
```

LangGraph 쪽에서는 이 주소들을 MCP Client에 등록한다. Docker 안에서는 `--host 0.0.0.0`과 서비스명을 사용하되 팀 아키텍처에 맞춰 내부망에서만 접근시킨다. 이 샘플에는 인증을 구현하지 않았으며 기본 호스트는 localhost이다.

## 요청 예시

`retrieve_repair_context`의 MCP arguments:

```json
{
  "request": {
    "raw_text": "흡입구에 먼지가 많아 보이고 전원이 켜지지 않아요.",
    "origin": "technician",
    "technician_confirmed": true,
    "pcb_labels": ["open_circuit", "hole missing"],
    "damage_labels": [
      {"damage_type": "damage", "part": "Headlight"},
      {"damage_type": "dent", "part": "bonnet"}
    ],
    "top_k": 5,
    "min_score": 0.75
  }
}
```

- PCB: `missing_hole`, `mouse_bite`, `open_circuit`, `short`, `spur`, `spurious_copper`.
- damage: `Front-windscreen`, `Headlight`, `Rear-windscreen`, `Runningboard`, `Sidemirror`, `Taillight`.
- dent: `bonnet`, `boot`, `doorouter`, `fender`, `front-bumper`, `quaterpanel`, `rear-bumper`, `roof`.
- `quarterpanel`은 별칭으로 허용하되 팀의 원본 표기 `quaterpanel`로 반환한다.
- 같은 부위라도 damage/dent 유형은 구분한다. 예: damage/roof는 미등록 값이다.
- 라벨 목록이 비었다고 정상 판정하지 않는다. 미등록 라벨은 버리지 않고 별도 반환한다.
- 점수/좌표/확정 원인을 전달받지 않았으므로 새로 생성하지 않는다.
- 기본적으로 인식된 표준 소견에 영문 용어를 붙여 다국어 검색을 돕는다. 부정과 추정 표시를 유지한다. `use_bilingual_hints=false`로 비교 실험할 수 있다.

### 자동차 라벨과 청소기 사례의 불일치

위 외형 라벨은 자동차 부위명이다. 청소기 전용 서비스이므로 이 라벨을 받으면 파손 MCP가 `domain_mismatch=true`를 반환한다. RAG는 해당 라벨의 **정의 문서와 원본 결과는 제공**하지만, 보닛을 청소기 덮개로 바꿔 사례 검색어에 넣지 않는다.

기사가 실제로 “본체가 찌그러졌어요”라고 입력한 소견은 독립적인 관찰로 검색에 사용한다. 자동차 부위 라벨과 이 관찰이 같은 위치라는 뜻은 아니다.

자동차 제품 검색 모드는 제공하지 않는다. 문서에 남아 있는 `product_domain`·`source_domain`은 원본 자료의 대상 제품을 설명하는 메타데이터이며 사용자가 선택하는 입력값이 아니다.

## 반환값을 사용하는 방법

- `observation`, `pcb`, `damage`: 입력별 해석과 출처.
- `repair_cases`: 출처 ID·URL·원문·기존 수리 상태·검색 점수를 가진 외부 사례.
- `label_definitions`: 정확한 라벨 ID로 찾은 정의. 유사 사례나 제조사 수리 지침이 아님.
- `pcb_references`: 별도로 검색된 기술 참고문서. 대상 제품이 다를 수 있음.
- `case_search_status=no_candidates`: 검색 후보 없음. 정상 제품 판정이 아님.
- `diagnosis_confirmed=false`: 이 단계는 확정 진단을 수행하지 않음.

LangGraph는 출처별 증거를 비교하고 추가 점검 필요성을 설명한다. 검색된 원문 안의 명령문을 시스템 지시로 실행하지 않는다. `Fixed`만 필요하면 `repair_status="Fixed"`를 전달하고, 그렇지 않으면 실패·수명 종료·결과 미상도 원래 상태로 반환한다.

## 색인 구성과 설정

- 사례: `all_cases.jsonl`만 색인. 기존 30건 샘플은 중복 색인하지 않는다.
- PCB: 기술 참고 3개 + 클래스 정의 6개.
- 외형: `data/damage_documents/labels.json`의 클래스 정의 14개.
- 토큰 기준 420개, 중첩 40개로 분할. 여러 청크가 검색되어도 같은 문서 ID는 한 번 반환한다.
- 문서·모델·리비전·청크 설정으로 컬렉션 이름에 fingerprint를 붙인다.
- 색인 완료 마커를 확인한다. 누락/불완전/입력 자료 변경 시 재색인 안내 오류를 반환한다.
- 색인은 자기 fingerprint 컬렉션에 upsert한다. 기존 다른 컬렉션을 삭제하지 않는다. 데이터 변경 시 과거 인덱스 정리는 운영자가 별도로 결정한다.

프로젝트 루트 `.env`를 자동 로드한다. 이미 설정된 쉘 또는 Docker 환경변수가 우선한다. `.env.example`은 빈 키와 설정 예시다.

| 환경변수 | 기본/용도 |
|---|---|
| OPENAI_API_KEY | 소견 변환용 키 |
| OPENAI_OBSERVATION_MODEL | gpt-4.1-mini; Responses 구조화 출력 지원 모델 |
| REPAIR_DATA_DIR | 프로젝트 data 경로 |
| REPAIR_RUNTIME_DIR | 프로젝트 .runtime 경로 |
| REPAIR_EMBED_MODEL | intfloat/multilingual-e5-small |
| REPAIR_EMBED_REVISION | 코드에 고정한 다운로드 리비전 |
| REPAIR_DEVICE | cpu; 환경에 따라 mps/cuda 사용 가능 |
| QDRANT_URL | 설정하지 않으면 로컬 Qdrant. 설정하면 외부 Qdrant 서버 사용 |
| QDRANT_API_KEY | 외부 Qdrant 인증 필요 시만 사용 |

다른 모델로 교체할 때는 해당 모델의 query/passage 접두어 규칙도 구현을 수정해야 한다. 단순 이름 변경만으로 모든 모델을 지원하는 것은 아니다. 배포 시 소스 외에 `data/`도 포함하고 경로를 설정한다.

## 현재 한계와 검증

소견 MCP는 OpenAI가 문맥을 읽고 표준 코드 중 후보를 선택한다. 코드 목록은 JSON Schema enum으로 제한하고 근거 원문을 검증한다. LLM도 복잡한 부정과 모호한 표현을 오분류할 수 있다. 미등록 표현은 원문으로 남기며 기사 확인 없이 확정 원인으로 저장하지 않는다. 키 미설정/API 실패 시 오류를 반환하며 규칙 방식으로 자동 전환하지 않는다.

Dense 검색의 기본 0.75 임계값은 임시값이다. E5의 점수는 0.7~1.0 부근에 몰릴 수 있으며 고장 확률이 아니다. 무관한 질문도 검색될 수 있다. 따라서 실제 신규 접수 질문에 대한 관련/무관 정답셋으로 임계값과 순위를 평가해야 한다. [모델 카드](https://huggingface.co/intfloat/multilingual-e5-small)는 query/passage 접두어와 점수 해석을 설명한다.

`experiments/results/summary.md`와 `retrieval.json`은 이전 규칙 기반 소견 변환의 실제 실행 결과다. OpenAI 전환 후 결과가 아니다. 키 등록 후 `experiments/run.py`를 실행하면 OpenAI 호출이 발생하고 `experiments/results/openai/`에 별도 저장된다. 반복 실행 시 그 하위 결과만 갱신한다. 모델의 독립 호출이므로 비교 간 변동성이 있으며 진단 정확도 평가가 아니다.

OpenAI 전환 후 검증: SDK HTTP 응답을 모의하여 요청 스키마·출처 보존·에러 처리·CLI·MCP 연결을 확인한다. 실제 OpenAI 호출은 키 등록 후 확인해야 한다. 이전 규칙 버전에서는 네 서버의 HTTP 호출과 실검색을 확인했다. `experiments/check_http.py`는 키 등록 후 재검증할 수 있으며 검증 후 임시 서버를 종료한다.

소견 MCP와 RAG를 각각 호출하면 OpenAI 변환도 두 번 실행된다. 두 응답은 같다고 보장하지 않는다. 검색만 필요하면 `retrieve_repair_context` 한 번으로 처리한다. 사용자 소견은 API에 전달하며 원본 사례 전체나 API 키를 프롬프트에 넣지 않는다.

## API 키를 넣었는데 인증 실패가 나는 경우

`.env`보다 기존 터미널의 `OPENAI_API_KEY` 환경변수가 우선한다. 오래된 키가 터미널에 남아 있다면 macOS/Linux에서 아래처럼 해당 실행에 한해 환경변수를 제외하고 `.env`의 키를 사용한다.

```bash
env -u OPENAI_API_KEY uv run repair-mcp normalize "흡입구에 먼지가 많은 것 같아요."
env -u OPENAI_API_KEY uv run python examples/call_mcp.py
```

실행 중인 MCP 서버에도 이전 키가 남아 있으므로 재시작해야 한다. 오류는 인증(401), 권한(403), 모델/경로(404), 할당량 부족(429 insufficient_quota), 요청 속도 제한(429), 연결 실패 등으로 구분한다. 제공업체의 원본 오류 본문과 키 값은 출력하지 않는다.
