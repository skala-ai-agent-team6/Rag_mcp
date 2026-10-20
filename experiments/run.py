"""Actual dense retrieval comparison, not a measured diagnosis-accuracy benchmark."""
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from fastmcp import Client
from repair_mcp.retrieval import DenseStore
from repair_mcp.servers import create_server

INPUTS = [
    {"name": "dust", "raw_text": "흡입구에 먼지가 많은 것 같아요", "pcb_labels": []},
    {"name": "no_power_open_circuit", "raw_text": "전원이 안 켜져요", "pcb_labels": ["open_circuit"]},
    {"name": "noise_short", "raw_text": "사용 중 큰 소음이 나고 멈춰요", "pcb_labels": ["short"]},
    {"name": "all_inputs", "raw_text": "본체가 찌그러졌고 전원이 안 켜져요",
     "pcb_labels": ["missing_hole"], "damage_labels": [{"damage_type": "dent", "part": "front-bumper"}]},
    {"name": "negative_filter", "raw_text": "필터는 막히지 않았고 흡입력이 약해요", "pcb_labels": []},
    {"name": "unknown_label_only", "raw_text": "", "pcb_labels": ["unregistered_class"]},
    {"name": "incompatible_damage_label_only", "raw_text": "",
     "damage_labels": [{"damage_type": "damage", "part": "Front-windscreen"}]},
]


async def main():
    store = DenseStore()
    output = {"run_at": datetime.now(timezone.utc).isoformat(),
              "model": store.model_name, "revision": store.revision, "fingerprint": store.fingerprint,
              "scope": "OpenAI extraction + real embeddings and Qdrant. Independent LLM calls can vary. No human relevance labels; scores are not accuracy.",
              "experiments": []}
    try:
        async with Client(create_server("rag", store), timeout=180) as client:
            for scenario in INPUTS:
                request = {k: v for k, v in scenario.items() if k != "name"}
                baseline = {**request, "pcb_labels": [], "damage_labels": []}
                korean = (await client.call_tool("retrieve_repair_context", {
                    "request": {**baseline, "use_bilingual_hints": False}})).data
                before = (await client.call_tool("retrieve_repair_context", {"request": baseline})).data
                after = (await client.call_tool("retrieve_repair_context", {"request": request})).data
                output["experiments"].append({"name": scenario["name"], "input": request,
                                              "korean_only": korean,
                                              "observation_only": before, "combined": after})
                print(scenario["name"], [x["document_id"] for x in after["repair_cases"]])
    finally:
        store.close()
    folder = Path(__file__).parent / "results" / "openai"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "retrieval.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    rows = ["# 실제 검색 실행 기록", "",
            f"- 임베딩: `{output['model']}` / `{output['revision']}`",
            f"- 실행 시각(UTC): {output['run_at']}",
            "- 한국어 소견만 입력한 결과와 소견+모델 라벨 결과를 비교했습니다.",
            "- 사람이 정답을 부여한 정확도 평가는 아닙니다. 원문/점수/출처는 retrieval.json에 보존합니다.",
            "- 영문 용어 확장 전/후 및 모델 라벨 결합 후를 같은 입력으로 실행했습니다.",
            "", "| 입력 | 한국어만 Top 1 | 영문 확장 소견 Top 1 | 라벨 결합 Top 1 | 정의 문서 수 |",
            "|---|---|---|---|---|"]
    for record in output["experiments"]:
        def top(result):
            cases = result["repair_cases"]
            return f"{cases[0]['document_id']} ({cases[0]['similarity_score']:.3f})" if cases else "없음"
        rows.append(f"| {record['name']} | {top(record['korean_only'])} | {top(record['observation_only'])} | {top(record['combined'])} | "
                    f"{len(record['combined']['label_definitions'])} |")
    rows += ["", "## 해석 시 주의", "",
             "- 라벨 추가로 순위가 달라져도 정확도가 좋아졌다는 뜻은 아닙니다.",
             "- 사례에 PCB 라벨 정답이 없으므로 결함 이름 일치 정확도를 계산하지 않습니다.",
             "- 자동차 부위 라벨은 청소기 검색어에서 제외되지만 정의와 원본 라벨은 반환됩니다.",
             "- 미등록 라벨만 있으면 사례 검색을 실행하지 않습니다.",
             "- 모델 정보가 없는 외부 사례이며 삼성 특정 모델의 확정 수리 지침이 아닙니다.",
             "- E5 점수의 임계값 0.75는 임시값입니다. 무관한 질문도 통과할 수 있어 정답셋 평가가 필요합니다.",
             "",
             "## 결과를 보고 확인할 항목",
             "",
             "- `dust`: 검색 결과의 먼지 위치가 흡입구와 일치하는지 확인한다.",
             "- `negative_filter`: 필터 막힘 부정과 모순되는 사례가 상위에 있는지 확인한다.",
             "- `no_power_open_circuit`: 전선/접촉 이상과 PCB 패턴 개방을 혼동하지 않는지 확인한다.",
             "- `all_inputs`: missing_hole 정의 문서를 확인된 수리 사례로 오해하지 않는지 확인한다.",
             "- 각 비교는 독립적인 OpenAI 호출이다. 정규화 출력의 차이도 함께 검토한다.",
             "- 모순 판별 재정렬과 기사 검토 정답셋 평가는 별도 작업이다."]
    (folder / "summary.md").write_text("\n".join(rows) + "\n")


asyncio.run(main())
