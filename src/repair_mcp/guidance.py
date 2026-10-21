"""Exact-label guidance lookup; no embedding or diagnosis generation."""
import json

from .config import DATA


def retrieve_guidance(pcb, damage):
    root = DATA / "label_guidance"
    policy = json.loads((root / "policy.json").read_text())
    policy["document_id"] = "guidance-policy"
    documents = [json.loads(line) for line in
                 (root / "guidance.jsonl").read_text().splitlines() if line.strip()]
    lookup = {(d["category"], d["label"]): d for d in documents}
    groups = {"pcb_guidance": [], "damage_guidance": []}
    missing = []
    for group, detections in (("pcb", pcb["detections"]), ("surface", damage["detections"])):
        for detection in detections:
            label = detection["label"]
            doc = lookup.get((group, label))
            if doc is None:
                missing.append({"category": group, "label": label})
                continue
            # Follow-up prompts remain in the source draft, but are not part of
            # the response contract or the text given to the report writer.
            public_doc = {key: value for key, value in doc.items()
                          if key != "follow_up_questions_ko"}
            question_heading = "\n## 기사에게 추가 확인\n"
            next_heading = "\n## 답변·실행 제한"
            if question_heading in public_doc["text"]:
                before, after = public_doc["text"].split(question_heading, 1)
                if next_heading in after:
                    public_doc["text"] = before + next_heading + after.split(next_heading, 1)[1]
            # These are review drafts, not approved instructions for automatic execution.
            groups["pcb_guidance" if group == "pcb" else "damage_guidance"].append({
                **public_doc, "match_type": "exact_label",
                "source_path": str((root / group / f"{label}.md").relative_to(DATA)),
                "usable_for_vacuum_inspection": group == "pcb" or (
                    group == "surface" and doc["applicability_status"] == "generic_surface_inspection_draft"),
                "requires_component_verification": True,
                "requires_human_approval": True,
                "diagnosis_confirmed": False,
            })
    return {**groups, "guidance_policy": policy, "missing_guidance": missing}


def symptom_conclusion(observation, pcb, damage):
    """Summarize the technician's reported symptoms in one short line."""
    present = list(dict.fromkeys(item["label_ko"] for item in observation.get("observations", [])
                                 if item["polarity"] == "present"))
    absent = list(dict.fromkeys(item["label_ko"] for item in observation.get("observations", [])
                                if item["polarity"] == "absent"))
    parts = []
    if present:
        parts.append(", ".join(present))
    elif not absent and observation.get("raw_text", "").strip():
        parts.append(observation["raw_text"].strip())
    if absent:
        parts.append(", ".join(absent) + "은 보이지 않는다고 보고")
    if not parts:
        labels = [f"PCB {item['label']}" for item in pcb["detections"]]
        labels += [f"외형 {item['label']}" for item in damage["detections"]]
        return "기사 소견 없음; 모델 라벨: " + ", ".join(labels) if labels else "입력 근거 없음"
    return "; ".join(parts)


def integrate_evidence(cases, references, guidance, observation, pcb, damage):
    """Return a symptom decision and traceable inspection guidance, without grading defects."""
    findings, proposals = [], []
    for group in ("pcb_guidance", "damage_guidance"):
        for doc in guidance[group]:
            available = doc["usable_for_vacuum_inspection"]
            findings.append({
                "category": doc["category"], "label": doc["label"],
                "meaning": doc["definition_ko"], "source_id": doc["document_id"],
                "diagnosis_confirmed": False,
                "applicability_status": doc["applicability_status"],
                "review_status": doc["review_status"],
                "action_status": "human_review_required" if available else "not_applicable",
            })
            if available:
                proposals.append({
                    "label": doc["label"], "source_id": doc["document_id"],
                    "inspection_steps": doc["inspection_steps_ko"],
                    "conditional_actions": doc["recommended_actions_ko"],
                    "status": "proposal_only", "requires_human_approval": True,
                })
    return {
        "method": "evidence_assembly_v1",
        "symptom_conclusion": symptom_conclusion(observation, pcb, damage),
        "summary": (
            f"유사 사례 {len(cases)}건, PCB 점검 지침 {len(guidance['pcb_guidance'])}건, "
            f"외형 점검 지침 {len(guidance['damage_guidance'])}건, 기술 참고문서 {len(references)}건을 반환합니다. "
            "고장 원인은 확정되지 않았습니다."
            + (" 외형 라벨만으로 위치·재질을 판단하지 않습니다." if damage["detections"] else "")
        ),
        "findings": findings,
        "case_evidence_ids": [c["document_id"] for c in cases],
        "technical_reference_ids": [d["document_id"] for d in references],
        "inspection_proposals": proposals,
        "unknown_labels": {"pcb": pcb["unknown_labels"], "damage": damage["unknown_labels"]},
        "assessment_scope": "symptom_triage_and_inspection",
        "diagnosis_confirmed": False,
        "requires_human_approval": True,
    }
