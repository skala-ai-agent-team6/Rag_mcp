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
