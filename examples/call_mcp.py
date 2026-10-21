"""Run after indexing: uv run python examples/call_mcp.py [--http] [--json]

The RAG tool accepts whichever inputs arrived and returns all interpretations.
Without --http it uses an in-memory MCP server; with --http it uses port 8014.
"""
import asyncio
import argparse
import json
from pathlib import Path
from fastmcp import Client
from repair_mcp.servers import create_server


def format_summary(result: dict) -> str:
    """Four concise report sections; --json retains full evidence and sources."""
    assessment = result.get("integrated_assessment")
    lines = ["[최종 소견]", " ".join(assessment["final_opinion"].split()), "", "[점검 안내]"]
    for proposal in assessment["inspection_proposals"]:
        first_step = proposal["inspection_steps"][0] if proposal["inspection_steps"] else "담당자 점검 지침 없음"
        lines.append(f"- {proposal['label']}: {first_step}")
    if not assessment["inspection_proposals"]:
        lines.append("- 입력된 모델 라벨의 점검 지침 없음")

    symptom = assessment["symptom_conclusion"]
    for key, name in (("pcb", "PCB"), ("damage", "외형")):
        if result[key]["input_state"] == "result_unavailable":
            symptom += f"; {name} 모델 결과 미전달"
    lines += ["", "[증상 판정]", symptom]

    cases = result.get("case_briefs", [])[:3]
    lines += ["", f"[유사 사례 {len(cases)}건 — 확정 진단 아님]"]
    lines += [f"{i}. {case['case_id']} | {case['summary']}"
              for i, case in enumerate(cases, 1)] if cases else ["검색 후보 없음"]
    return "\n".join(lines)


async def main():
    parser = argparse.ArgumentParser(description="기사 소견·모델 라벨 해석 및 사례 검색")
    parser.add_argument("--http", action="store_true", help="실행 중인 RAG HTTP MCP 서버에 연결")
    parser.add_argument("--json", action="store_true", help="RAG MCP의 전체 JSON 응답 출력")
    args = parser.parse_args()
    payload = json.loads((Path(__file__).parent / "search_request.json").read_text())
    target = "http://127.0.0.1:8014/mcp" if args.http else create_server("rag")
    async with Client(target, timeout=180) as client:
        result = (await client.call_tool("retrieve_repair_context", {"request": payload})).data
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else format_summary(result))


if __name__ == "__main__":
    asyncio.run(main())
