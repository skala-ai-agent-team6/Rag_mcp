import pytest
from pydantic import ValidationError
from repair_mcp.labels import SURFACE_DEFECTS, interpret_damage_labels, interpret_pcb_labels
from repair_mcp.models import SearchRequest
from repair_mcp.retrieval import prepare_query


def test_pcb_aliases_unknown_and_empty():
    result = interpret_pcb_labels(["hole missing", "MISSING-HOLE", "unknown"])
    assert len(result["detections"]) == 1
    assert result["detections"][0]["label"] == "missing_hole"
    assert result["unknown_labels"] == ["unknown"]
    assert interpret_pcb_labels([])["input_state"] == "no_labels_provided"


@pytest.mark.parametrize("label", SURFACE_DEFECTS)
def test_every_surface_label(label):
    result = interpret_damage_labels([label])
    assert result["detections"][0]["label"] == label
    assert result["detections"][0]["location"] is None
    assert result["detections"][0]["target_component"] is None


def test_surface_alias_format_duplicates_and_legacy_unknown():
    result = interpret_damage_labels(["Rolled In Scale", "rolled-in_scale", "roof"])
    assert [d["label"] for d in result["detections"]] == ["rolled-in_scale"]
    assert result["detections"][0]["raw_label"] == "Rolled In Scale"
    assert result["unknown_labels"] == ["roof"]
    assert interpret_damage_labels([])["input_state"] == "no_labels_provided"


def test_search_request_accepts_label_strings_but_not_legacy_part_objects():
    assert "product_domain" not in SearchRequest.model_json_schema()["properties"]
    with pytest.raises(ValidationError):
        SearchRequest(product_domain="automotive")
    with pytest.raises(ValidationError):
        SearchRequest(damage_labels=[{"damage_type": "dent", "part": "roof"}])


def test_combination_uses_surface_defect_without_inventing_part(monkeypatch):
    monkeypatch.setattr("repair_mcp.retrieval.normalize_observations", lambda *args: {"observations": []})
    request = SearchRequest(raw_text="표면에 잔금이 보여요", pcb_labels=["open circuit"],
                            damage_labels=["crazing"])
    query, obs, pcb, damage, warnings = prepare_query(request)
    assert "잔금" in query and "open_circuit" in query
    assert "crazing" in query and "상단 커버" not in query
    assert damage["detections"][0]["location"] is None
    assert any("좌표" in warning for warning in warnings)


def test_negative_observation_not_expanded_positive(monkeypatch):
    monkeypatch.setattr("repair_mcp.retrieval.normalize_observations", lambda *args: {"observations": [{
        "polarity": "absent", "certainty": "reported", "label_ko": "필터 오염", "search_hint_en": "dirty filter"}]})
    query, *_ = prepare_query(SearchRequest(raw_text="필터에 먼지는 없어요"))
    assert "not observed: dirty filter" in query
    assert "reported: dirty filter" not in query
