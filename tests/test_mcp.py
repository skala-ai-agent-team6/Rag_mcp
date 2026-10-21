import pytest
from fastmcp import Client
from repair_mcp.servers import create_server
from repair_mcp.models import SearchRequest
from repair_mcp.retrieval import retrieve_context
from examples.call_mcp import format_summary


@pytest.mark.parametrize("service,tool,payload,key", [
    ("observation", "normalize_observation", {"raw_text": "흡입구에 먼지가 많아요"}, "observations"),
    ("pcb", "interpret_pcb", {"labels": ["short"]}, "detections"),
    ("damage", "interpret_damage", {"labels": ["crazing"]}, "detections"),
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
            "labels": [{"damage_type": "dent", "part": "roof"}]}, raise_on_error=False)
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


async def test_rag_combines_cases_and_exact_surface_guidance_without_inventing_location(monkeypatch):
    class EvidenceStore(EmptyStore):
        def search(self, group, query, *args):
            assert "mouse_bite" in query
            assert "crazing: " in query
            return [{"document_id": "case:known", "source_repair_status": "Fixed"}] if group == "repair_cases" else []

    monkeypatch.setattr("repair_mcp.retrieval.normalize_observations", lambda *args: {
        "raw_text": "전원이 안 켜집니다", "observations": []})
    async with Client(create_server("rag", EvidenceStore())) as client:
        result = (await client.call_tool("retrieve_repair_context", {"request": {
            "raw_text": "전원이 안 켜집니다", "pcb_labels": ["mouse bite", "mouse_bite"],
            "damage_labels": ["crazing"],
        }})).data
    assert len(result["pcb_guidance"]) == 1
    assert result["pcb_guidance"][0]["label"] == "mouse_bite"
    surface = result["damage_guidance"][0]
    assert surface["label"] == "crazing"
    assert surface["usable_for_vacuum_inspection"] is True
    assert surface["applicability_status"] == "generic_surface_inspection_draft"
    assert result["damage"]["detections"][0]["location"] is None
    assessment = result["integrated_assessment"]
    assert assessment["case_evidence_ids"] == ["case:known"]
    assert assessment["assessment_scope"] == "symptom_triage_and_inspection"
    assert "전원이 안 켜집니다" in assessment["symptom_conclusion"]
    assert "additional_questions" not in assessment
    assert "severity" not in assessment
    assert {p["label"] for p in assessment["inspection_proposals"]} == {"mouse_bite", "crazing"}
    assert all("severity" not in f and not f["diagnosis_confirmed"] for f in assessment["findings"])
    assert "잔금" in surface["text"]


async def test_all_twelve_guides_available_even_without_similar_cases():
    pcb = ["missing_hole", "mouse_bite", "open_circuit", "short", "spur", "spurious_copper"]
    surface = ["crazing", "inclusion", "patches", "pitted_surface", "rolled-in_scale", "scratches"]
    async with Client(create_server("rag", EmptyStore())) as client:
        result = (await client.call_tool("retrieve_repair_context", {"request": {
            "pcb_labels": pcb + ["unknown"], "damage_labels": surface,
        }})).data
    assert result["case_search_status"] == "no_candidates"
    assert {g["label"] for g in result["pcb_guidance"]} == set(pcb)
    assert {g["label"] for g in result["damage_guidance"]} == set(surface)
    assert result["integrated_assessment"]["unknown_labels"]["pcb"] == ["unknown"]
    assert result["missing_guidance"] == []
    assert all("follow_up_questions_ko" not in guide and "기사에게 추가 확인" not in guide["text"]
               for guide in result["pcb_guidance"] + result["damage_guidance"])


def test_label_only_report_shows_inspection_guidance_without_grade():
    result = retrieve_context(SearchRequest(
        pcb_labels=["mouse_bite"], damage_labels=["crazing"]), EmptyStore())
    report = format_summary(result)

    assert "[증상 판정]" in report
    assert "PCB 모델 검출: mouse_bite" in report
    assert "외형 모델 검출: crazing" in report
    assert "[점검 안내]" in report
    assert "[mouse_bite 확인 순서]" in report
    assert "[crazing 확인 순서]" in report
    assert "[추가 확인 질문]" not in report
    assert "심각도" not in report
    assert "중요도" not in report
    assert "판단 보류" not in report
