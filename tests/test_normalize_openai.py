"""Offline SDK contract tests using fabricated HTTP responses, not AI quality tests."""
import json
import httpx
import pytest
from openai import OpenAI
from repair_mcp import normalize


@pytest.fixture
def fake_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    monkeypatch.setenv("OPENAI_OBSERVATION_MODEL", "gpt-4.1-mini")
    requests = []

    def install(output=None, status="completed", http_status=200, refusal=False, error_code=None):
        def handle(request):
            requests.append(json.loads(request.content))
            if http_status != 200:
                return httpx.Response(http_status, json={"error": {"message": "provider-secret-detail", "type": "invalid_request_error", "code": error_code}})
            content = [{"type": "refusal", "refusal": "cannot process"}] if refusal else [
                {"type": "output_text", "text": json.dumps(output or {"observations": [], "unmapped_fragments": []}), "annotations": []}]
            return httpx.Response(200, json={
                "id": "resp_test", "object": "response", "created_at": 1,
                "model": "gpt-4.1-mini", "status": status,
                "output": [{"id": "msg_test", "type": "message", "role": "assistant",
                            "status": "completed", "content": content}]})
        monkeypatch.setattr(normalize, "OpenAI", lambda **kwargs: OpenAI(
            **kwargs, http_client=httpx.Client(transport=httpx.MockTransport(handle))))
        return requests
    return install


def observation(code="INLET_DUST_EXCESS", evidence="흡입구에 먼지가 많은 것 같아요", **overrides):
    return {"code": code, "evidence_text": evidence, "polarity": "present", "certainty": "suspected", **overrides}


def test_sdk_request_and_provenance(fake_openai):
    requests = fake_openai({"observations": [observation()], "unmapped_fragments": []})
    text = "흡입구에 먼지가 많은 것 같아요"
    result = normalize.normalize_observations(text, "ai_image")
    assert result["observations"][0]["code"] == "INLET_DUST_EXCESS"
    assert result["observations"][0]["search_hint_en"] == "dust accumulation at suction inlet"
    assert result["origin"] == "ai_image" and not result["technician_confirmed"]
    assert result["engine"] == "openai-structured-output-v1"
    assert requests[0]["input"][1] == {"role": "user", "content": text}
    assert requests[0]["store"] is False
    schema = requests[0]["text"]["format"]["schema"]
    assert len(schema["$defs"]["ObservationCode"]["enum"]) == 43
    assert "HOUSING_CRACK" in schema["$defs"]["ObservationCode"]["enum"]


def test_negative_and_uncertainty_preserved(fake_openai):
    item = observation("FILTER_BLOCKED", "필터는 막히지 않았어요", polarity="absent", certainty="reported")
    fake_openai({"observations": [item], "unmapped_fragments": []})
    result = normalize.normalize_observations(item["evidence_text"])
    assert result["observations"][0]["polarity"] == "absent"
    assert result["observations"][0]["certainty"] == "reported"


def test_unmapped_and_no_diagnosis(fake_openai):
    fake_openai()
    result = normalize.normalize_observations("처음 보는 현상")
    assert result["unmapped_fragments"] == ["처음 보는 현상"]
    assert result["observations"] == [] and not result["diagnosis_confirmed"]


@pytest.mark.parametrize("output", [
    {"observations": [observation(evidence="없는 근거")], "unmapped_fragments": []},
    {"observations": [], "unmapped_fragments": ["없는 구절"]},
    {"observations": [observation(code="INVENTED")], "unmapped_fragments": []},
])
def test_rejects_untrusted_output(fake_openai, output):
    fake_openai(output)
    with pytest.raises(RuntimeError):
        normalize.normalize_observations("흡입구에 먼지가 많은 것 같아요")


@pytest.mark.parametrize("settings", [{"status": "incomplete"}, {"refusal": True}, {"http_status": 401}])
def test_provider_failures_not_silent_fallback(fake_openai, settings):
    fake_openai(**settings)
    with pytest.raises(RuntimeError) as error:
        normalize.normalize_observations("흡입구에 먼지가 많아요")
    assert "provider-secret-detail" not in str(error.value)
    assert "test-key" not in str(error.value)


def test_missing_key_clear_error(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        normalize.normalize_observations("흡입구에 먼지가 많아요")


@pytest.mark.parametrize("status,code,expected", [
    (401, "invalid_api_key", "401 authentication"),
    (403, None, "403 permission"),
    (404, "model_not_found", "404 model_or_endpoint"),
    (429, "insufficient_quota", "429 insufficient_quota"),
    (429, "rate_limit_exceeded", "429 rate_limit"),
    (400, "invalid_json_schema", "400 invalid_json_schema"),
    (400, None, "400 request"),
    (500, None, "server_error"),
])
def test_error_classification(fake_openai, status, code, expected):
    fake_openai(http_status=status, error_code=code)
    with pytest.raises(RuntimeError, match=expected) as error:
        normalize.normalize_observations("흡입구에 먼지가 많아요")
    assert "provider-secret-detail" not in str(error.value)


def test_invalid_input_before_api(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        normalize.normalize_observations(" ")


def test_normalize_cli_uses_sdk(fake_openai, monkeypatch, capsys):
    from repair_mcp.cli import main
    requests = fake_openai({"observations": [observation()], "unmapped_fragments": []})
    monkeypatch.setattr("sys.argv", ["repair-mcp", "normalize", "흡입구에 먼지가 많은 것 같아요"])
    main()
    assert json.loads(capsys.readouterr().out)["engine"] == "openai-structured-output-v1"
    assert len(requests) == 1
