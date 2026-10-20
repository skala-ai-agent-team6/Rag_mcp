import pytest
from fastmcp import Client
from repair_mcp.servers import create_server


@pytest.mark.parametrize("service,tool,payload,key", [
    ("observation", "normalize_observation", {"raw_text": "흡입구에 먼지가 많아요"}, "observations"),
    ("pcb", "interpret_pcb", {"labels": ["short"]}, "detections"),
    ("damage", "interpret_damage", {"labels": [{"damage_type": "dent", "part": "roof"}]}, "detections"),
])
async def test_protocol(service, tool, payload, key, monkeypatch):
    monkeypatch.setattr("repair_mcp.servers.normalize_observations", lambda *args: {
        "observations": [{"code": "INLET_DUST_EXCESS"}], "engine": "test-stub"})
    async with Client(create_server(service)) as client:
        tools = await client.list_tools()
        assert any(t.name == tool and t.annotations.readOnlyHint for t in tools)
        result = await client.call_tool(tool, payload)
        assert result.data[key]


async def test_validation_through_protocol():
    async with Client(create_server("damage")) as client:
        result = await client.call_tool("interpret_damage", {
            "labels": [{"damage_type": "bogus", "part": "roof"}]}, raise_on_error=False)
        assert result.is_error


async def test_damage_mcp_has_no_product_selector():
    async with Client(create_server("damage")) as client:
        tools = await client.list_tools()
        tool = next(t for t in tools if t.name == "interpret_damage")
        assert "product_domain" not in tool.inputSchema["properties"]


class EmptyStore:
    documents = {"pcb_documents": [], "damage_documents": []}
    def search(self, *args):
        return []


async def test_rag_protocol_empty_result_honest(monkeypatch):
    monkeypatch.setattr("repair_mcp.retrieval.normalize_observations", lambda *args: {"observations": []})
    async with Client(create_server("rag", EmptyStore())) as client:
        result = await client.call_tool("retrieve_repair_context", {"request": {"raw_text": "전원이 안 켜져요"}})
        assert result.data["case_search_status"] == "no_candidates"
        assert result.data["diagnosis_confirmed"] is False


async def test_rag_combines_cases_and_exact_guidance_without_inventing_applicability(monkeypatch):
    class EvidenceStore(EmptyStore):
        def search(self, group, query, *args):
            assert "mouse_bite" in query
            assert "quaterpanel" not in query
            return [{"document_id": "case:known", "source_repair_status": "Fixed"}] if group == "repair_cases" else []

    monkeypatch.setattr("repair_mcp.retrieval.normalize_observations", lambda *args: {
        "raw_text": "전원이 안 켜집니다", "observations": []})
    async with Client(create_server("rag", EvidenceStore())) as client:
        result = (await client.call_tool("retrieve_repair_context", {"request": {
            "raw_text": "전원이 안 켜집니다", "pcb_labels": ["mouse bite", "mouse_bite"],
            "damage_labels": [{"damage_type": "dent", "part": "quarterpanel"}],
        }})).data
    assert len(result["pcb_guidance"]) == 1
    assert result["pcb_guidance"][0]["label"] == "mouse_bite"
    dent = result["damage_guidance"][0]
    assert dent["label"] == "quaterpanel"
    assert dent["usable_for_vacuum_action"] is False
    assert dent["applicability_status"] == "awaiting_vacuum_mapping"
    assessment = result["integrated_assessment"]
    assert assessment["case_evidence_ids"] == ["case:known"]
    assert assessment["severity"] == "U"
    assert all(p["label"] == "mouse_bite" for p in assessment["inspection_proposals"])
    assert all(f["severity"] == "U" and not f["diagnosis_confirmed"] for f in assessment["findings"])
    assert "자동차 부위 기준" in dent["text"]


async def test_all_twelve_guides_available_even_without_similar_cases():
    pcb = ["missing_hole", "mouse_bite", "open_circuit", "short", "spur", "spurious_copper"]
    dent = ["boot", "doorouter", "fender", "front-bumper", "quaterpanel", "roof"]
    async with Client(create_server("rag", EmptyStore())) as client:
        result = (await client.call_tool("retrieve_repair_context", {"request": {
            "pcb_labels": pcb + ["unknown"], "damage_labels": [
                {"damage_type": "dent", "part": p} for p in dent],
        }})).data
    assert result["case_search_status"] == "no_candidates"
    assert {g["label"] for g in result["pcb_guidance"]} == set(pcb)
    assert {g["label"] for g in result["damage_guidance"]} == set(dent)
    assert result["integrated_assessment"]["unknown_labels"]["pcb"] == ["unknown"]
    assert result["missing_guidance"] == []
