import json
from types import SimpleNamespace

import pytest

from repair_mcp import opinion


def sample_evidence():
    observation = {"raw_text": "간헐적으로 멈추지만 필터는 막히지 않았어요", "observations": [
        {"label_ko": "간헐적 꺼짐", "polarity": "present", "certainty": "reported"},
        {"label_ko": "필터 막힘", "polarity": "absent", "certainty": "reported"},
    ]}
    pcb = {"detections": [{"label": "mouse_bite"}]}
    damage = {"detections": [{"label": "crazing"}]}
    cases = [{"document_id": "case:1", "source_repair_status": "Fixed",
              "original_text": "Board contact repaired."}]
    guidance = {"pcb_guidance": [{"label": "mouse_bite", "definition_ko": "패턴 가장자리 결손",
                               "inspection_steps_ko": ["패턴 연속성을 확인한다."]}],
                "damage_guidance": [{"label": "crazing", "definition_ko": "가는 균열 후보",
                                  "inspection_steps_ko": ["표면을 확인한다."]}]}
    return observation, pcb, damage, cases, guidance


def install_fake_client(monkeypatch, parsed):
    calls = []

    class FakeClient:
        def __init__(self, **kwargs):
            self.responses = SimpleNamespace(parse=self.parse)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def parse(self, **kwargs):
            calls.append(kwargs)
            output = parsed.pop(0) if isinstance(parsed, list) else parsed
            return SimpleNamespace(status="completed", output_parsed=output)

    monkeypatch.setattr(opinion, "OpenAI", FakeClient)
    return calls


def test_llm_opinion_excludes_negated_input_and_unfiltered_cases(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    calls = install_fake_client(monkeypatch, opinion.FinalOpinion(
        opinion_ko="PCB 패턴을 우선 확인하고 외형 균열을 점검합니다.",
        supporting_case_ids=[]))
    result = opinion.generate_final_opinion(*sample_evidence())

    assert result["text"] == "PCB 패턴을 우선 확인하고 외형 균열을 점검합니다."
    assert result["supporting_case_ids"] == []
    assert result["engine"] == "openai-structured-output-v1"
    assert calls[0]["store"] is False
    evidence = json.loads(calls[0]["input"][1]["content"])
    assert evidence["reported_symptoms"][0]["label_ko"] == "간헐적 꺼짐"
    assert evidence["similar_cases"] == []
    assert "필터" not in calls[0]["input"][1]["content"]
    assert evidence["inspection_guidance"][0]["first_step"] == "패턴 연속성을 확인한다."


def test_llm_opinion_can_cite_case_without_negative_report(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    calls = install_fake_client(monkeypatch, opinion.FinalOpinion(
        opinion_ko="PCB 패턴을 확인합니다.", supporting_case_ids=["case:1"]))
    observation, pcb, damage, cases, guidance = sample_evidence()
    observation["observations"] = observation["observations"][:1]
    result = opinion.generate_final_opinion(observation, pcb, damage, cases, guidance)
    assert result["supporting_case_ids"] == ["case:1"]
    evidence = json.loads(calls[0]["input"][1]["content"])
    assert evidence["similar_cases"][0]["id"] == "case:1"


def test_filter_negative_removes_filter_cases_but_retains_other_cases(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    calls = install_fake_client(monkeypatch, opinion.FinalOpinion(
        opinion_ko="PCB 패턴을 확인합니다.", supporting_case_ids=["case:1"]))
    observation, pcb, damage, cases, guidance = sample_evidence()
    observation["observations"][1]["code"] = "FILTER_BLOCKED"
    cases[0]["source_fault_type"] = "Internal damage"
    cases.insert(0, {"document_id": "case:filter", "source_fault_type": "Filter",
                     "original_text": "Filter blocked and cleaned."})
    result = opinion.generate_final_opinion(observation, pcb, damage, cases, guidance)
    evidence = json.loads(calls[0]["input"][1]["content"])
    assert result["supporting_case_ids"] == ["case:1"]
    assert [case["id"] for case in evidence["similar_cases"]] == ["case:1"]


@pytest.mark.parametrize("text,case_ids", [
    ("추가 사진을 보내실 수 있나요?", []),
    ("PCB를 점검합니다.", ["case:not-provided"]),
    ("필터 점검은 제외합니다.", []),
])
def test_llm_opinion_rejects_question_or_invented_case(monkeypatch, text, case_ids):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    install_fake_client(monkeypatch, opinion.FinalOpinion(
        opinion_ko=text, supporting_case_ids=case_ids))
    with pytest.raises(RuntimeError):
        opinion.generate_final_opinion(*sample_evidence())


def test_llm_opinion_retries_when_negative_symptom_is_treated_as_fact(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    calls = install_fake_client(monkeypatch, [
        opinion.FinalOpinion(opinion_ko="필터 점검을 제외합니다.", supporting_case_ids=[]),
        opinion.FinalOpinion(opinion_ko="간헐적 정지에 대해 PCB 패턴과 외형 균열을 점검합니다.",
                             supporting_case_ids=[]),
    ])
    result = opinion.generate_final_opinion(*sample_evidence())
    assert len(calls) == 2
    assert "필터" not in result["text"]


def test_llm_opinion_is_one_line_even_if_response_contains_newline(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    install_fake_client(monkeypatch, opinion.FinalOpinion(
        opinion_ko="PCB 패턴을 확인하고\n외형 균열을 점검합니다.", supporting_case_ids=[]))
    result = opinion.generate_final_opinion(*sample_evidence())
    assert result["text"] == "PCB 패턴을 확인하고 외형 균열을 점검합니다."


def test_unmapped_technician_report_reaches_opinion_when_models_are_missing(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    calls = install_fake_client(monkeypatch, opinion.FinalOpinion(
        opinion_ko="보고된 작동 이상을 점검합니다.", supporting_case_ids=[]))
    observation = {"raw_text": "동작이 이상해요", "observations": []}
    pcb, damage = {"detections": []}, {"detections": []}
    guidance = {"pcb_guidance": [], "damage_guidance": []}
    opinion.generate_final_opinion(observation, pcb, damage, [], guidance)
    evidence = json.loads(calls[0]["input"][1]["content"])
    assert evidence["unmapped_report"] == "동작이 이상해요"
