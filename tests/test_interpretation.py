import pytest
from pydantic import ValidationError
from repair_mcp.labels import DAMAGE_PARTS, interpret_damage_labels, interpret_pcb_labels
from repair_mcp.models import DamageLabel, SearchRequest
from repair_mcp.retrieval import prepare_query


def test_pcb_aliases_unknown_and_empty():
    result = interpret_pcb_labels(["hole missing", "MISSING-HOLE", "unknown"])
    assert len(result["detections"]) == 1
    assert result["detections"][0]["label"] == "missing_hole"
    assert result["unknown_labels"] == ["unknown"]
    assert interpret_pcb_labels([])["input_state"] == "no_labels_provided"


@pytest.mark.parametrize("kind,part", [(k, p) for k, ps in DAMAGE_PARTS.items() for p in ps])
def test_every_damage_label(kind, part):
    result = interpret_damage_labels([DamageLabel(damage_type=kind, part=part)])
    assert result["detections"][0]["part"] == part
    assert result["domain_mismatch"]


def test_category_sensitive_and_alias():
    result = interpret_damage_labels([
        DamageLabel(damage_type="damage", part="roof"),
        DamageLabel(damage_type="dent", part="quarterpanel")])
    assert result["unknown_labels"] == [{"damage_type": "damage", "part": "roof"}]
    assert result["detections"][0]["part"] == "quaterpanel"
    assert result["domain_mismatch"]
    with pytest.raises(ValidationError):
        DamageLabel(damage_type="broken", part="roof")


def test_search_request_has_no_product_selector():
    assert "product_domain" not in SearchRequest.model_json_schema()["properties"]
    with pytest.raises(ValidationError):
        SearchRequest(product_domain="automotive")


def test_combination_preserves_but_does_not_remap_car_part(monkeypatch):
    monkeypatch.setattr("repair_mcp.retrieval.normalize_observations", lambda *args: {"observations": []})
    request = SearchRequest(raw_text="흡입구에 먼지가 많아 보여요", pcb_labels=["open circuit"],
                            damage_labels=[DamageLabel(damage_type="dent", part="roof")])
    query, obs, pcb, damage, warnings = prepare_query(request)
    assert "흡입구" in query and "open_circuit" in query
    assert "roof" not in query and "지붕" not in query
    assert damage["detections"][0]["raw_part"] == "roof"
    assert warnings


def test_removed_exterior_classes_are_preserved_as_unknown():
    values = [DamageLabel(damage_type="damage", part="Headlight"),
              DamageLabel(damage_type="dent", part="bonnet"),
              DamageLabel(damage_type="dent", part="rear-bumper")]
    result = interpret_damage_labels(values)
    assert result["detections"] == []
    assert result["unknown_labels"] == [v.model_dump() for v in values]


def test_negative_observation_not_expanded_positive(monkeypatch):
    monkeypatch.setattr("repair_mcp.retrieval.normalize_observations", lambda *args: {"observations": [{
        "polarity": "absent", "certainty": "reported", "label_ko": "필터 오염", "search_hint_en": "dirty filter"}]})
    query, *_ = prepare_query(SearchRequest(raw_text="필터에 먼지는 없어요"))
    assert "not observed: dirty filter" in query
    assert "reported: dirty filter" not in query
