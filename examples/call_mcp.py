"""Run after indexing: uv run python examples/call_mcp.py [--http] [--json]

Without --http: four real MCP clients use in-memory transports.
With --http: connect to the four running Streamable HTTP services.
"""
import asyncio
import argparse
import json
from pathlib import Path
from fastmcp import Client
from repair_mcp.servers import create_server


def format_summary(result: dict) -> str:
    """Readable view of RAG evidence; does not change ranking or generate a diagnosis."""
    observation = result["observation"]
    lines = ["[입력 소견]", observation["raw_text"] or "(소견 없음)", "", "[입력 해석]"]
    for item in observation["observations"]:
        polarity = "없음" if item["polarity"] == "absent" else "있음"
        certainty = "추정" if item["certainty"] == "suspected" else "보고"
        lines.append(f"- {item['label_ko']} ({polarity}, {certainty})")
    for text in observation.get("unmapped_fragments", []):
        lines.append(f"- 미분류 소견: {text}")
    for item in result["pcb"]["detections"]:
        lines.append(f"- PCB: {item['label']} — {item['description_ko']}")
    for item in result["damage"]["detections"]:
        suffix = "" if item["domain_compatible"] else " / 청소기 부위와 불일치, 검색어 제외"
        lines.append(f"- 외형: {item['description_ko']}{suffix}")
    for category in ("pcb", "damage"):
        if result[category]["unknown_labels"]:
            lines.append(f"- {category} 미등록 라벨: {result[category]['unknown_labels']}")

    cases = result["repair_cases"]
    lines += ["", f"[검색된 사례 {len(cases)}건 — 확정 진단 아님]"]
    statuses = {"Fixed": "수리 완료", "Repairable": "수리 가능",
                "End of life": "수명 종료", "Unknown": "결과 미상"}
    if not cases:
        lines.append("검색 후보 없음")
    for i, case in enumerate(cases, 1):
        status = statuses.get(case.get("source_repair_status"), "결과 미상")
        text = " ".join(case["original_text"].split())
        excerpt = text[:220] + ("…" if len(text) > 220 else "")
        lines += [f"{i}. {case['document_id']} | {status} | 유사도 {case['similarity_score']:.3f}",
                  f"   원문 발췌: {excerpt}"]
    urls = list(dict.fromkeys(c["source_url"] for c in cases if c.get("source_url")))
    if urls:
        lines += ["사례 출처: " + " / ".join(urls)]

    references = result["pcb_references"]
    if references:
        lines += ["", "[참고문서 — 다른 제품 자료 포함, 적용 여부 확인 필요]"]
        lines += [f"- {doc.get('title', doc['document_id'])}" for doc in references]
    assessment = result.get("integrated_assessment")
    if assessment:
        lines += ["", "[종합 근거]", assessment["summary"]]
        for finding in assessment["findings"]:
            lines.append(f"- {finding['label']}: {finding['meaning']} "
                         f"| 심각도 판단 보류 | {finding['action_status']}")
        lines += ["", "[추가 확인]"]
        lines += [f"- {item['question']} ({item['source_id']})"
                  for item in assessment["additional_questions"]]
        for proposal in assessment["inspection_proposals"]:
            lines += ["", f"[{proposal['label']} 점검 제안 — 담당자 확인·승인 필요]"]
            lines += [f"- {step}" for step in proposal["inspection_steps"]]
    lines += ["", "[해석 시 주의]"]
    lines += [f"- {warning}" for warning in result["warnings"]]
    lines += ["", "전체 원문·출처·라벨 정의·중간 응답: 같은 명령에 --json 추가"]
    return "\n".join(lines)


async def main():
    parser = argparse.ArgumentParser(description="기사 소견·모델 라벨 해석 및 사례 검색")
    parser.add_argument("--http", action="store_true", help="실행 중인 네 HTTP MCP 서버에 연결")
    parser.add_argument("--json", action="store_true", help="네 MCP의 전체 JSON 응답 출력")
    args = parser.parse_args()
    payload = json.loads((Path(__file__).parent / "search_request.json").read_text())
    calls = [
        ("observation", "normalize_observation", {k: payload[k] for k in
            ("raw_text", "origin", "technician_confirmed")}),
        ("pcb", "interpret_pcb", {"labels": payload["pcb_labels"]}),
        ("damage", "interpret_damage", {"labels": payload["damage_labels"]}),
        ("rag", "retrieve_repair_context", {"request": payload}),
    ]
    results = {}
    for i, (service, tool, arguments) in enumerate(calls):
        target = f"http://127.0.0.1:{8011 + i}/mcp" if args.http else create_server(service)
        async with Client(target, timeout=180) as client:
            results[service] = (await client.call_tool(tool, arguments)).data
    # RAG accepts raw inputs and makes its own OpenAI normalization call.
    # Never discard unknown/negative evidence to feed only positive codes.
    # These are independent LLM calls: classifications may differ.
    assert results["observation"]["raw_text"] == results["rag"]["observation"]["raw_text"]
    print(json.dumps(results, ensure_ascii=False, indent=2) if args.json else format_summary(results["rag"]))


if __name__ == "__main__":
    asyncio.run(main())
