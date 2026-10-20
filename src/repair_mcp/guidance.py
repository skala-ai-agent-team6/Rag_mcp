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
    for group, detections in (("pcb", pcb["detections"]), ("dent", damage["detections"])):
        for detection in detections:
            label = detection["label"] if group == "pcb" else detection["part"]
            doc = lookup.get((group, label))
            if doc is None:
                missing.append({"category": group, "label": label})
                continue
            # These are review drafts, not approved instructions for automatic execution.
            groups["pcb_guidance" if group == "pcb" else "damage_guidance"].append({
                **doc, "match_type": "exact_label",
                "source_path": str((root / group / f"{label}.md").relative_to(DATA)),
                "usable_for_vacuum_action": group == "pcb",
                "requires_component_verification": True,
                "requires_human_approval": True,
                "diagnosis_confirmed": False,
            })
    return {**groups, "guidance_policy": policy, "missing_guidance": missing}


def integrate_evidence(cases, references, guidance, pcb, damage):
    """Assemble traceable findings and questions, keeping unknown severity explicit."""
    findings, questions, proposals = [], [], []
    for group in ("pcb_guidance", "damage_guidance"):
        for doc in guidance[group]:
            available = doc["usable_for_vacuum_action"]
            findings.append({
                "category": doc["category"], "label": doc["label"],
                "meaning": doc["definition_ko"], "source_id": doc["document_id"],
                "severity": "U", "diagnosis_confirmed": False,
                "applicability_status": doc["applicability_status"],
                "review_status": doc["review_status"],
                "action_status": "human_review_required" if available else "awaiting_vacuum_mapping",
            })
            if available:
                questions.extend({"question": q, "source_id": doc["document_id"]}
                                 for q in doc["follow_up_questions_ko"])
                proposals.append({
                    "label": doc["label"], "source_id": doc["document_id"],
                    "inspection_steps": doc["inspection_steps_ko"],
                    "conditional_actions": doc["recommended_actions_ko"],
                    "status": "proposal_only", "requires_human_approval": True,
                })
    if damage["detections"]:
        questions.append({
            "question": "외형 라벨에 대응하는 청소기 부위와 실제 변형·간섭·기능 정보를 확인해 주세요.",
            "source_id": guidance["guidance_policy"]["document_id"],
        })
    return {
        "method": "evidence_assembly_v1",
        "summary": (
            f"유사 사례 {len(cases)}건, PCB 점검 지침 {len(guidance['pcb_guidance'])}건, "
            f"외형 점검 지침 {len(guidance['damage_guidance'])}건, 기술 참고문서 {len(references)}건을 반환합니다. "
            "고장 원인과 심각도는 확정되지 않았습니다."
            + (" 외형 지침은 청소기 대응표 확인 전까지 조치에 적용하지 않습니다."
               if damage["detections"] else "")
        ),
        "findings": findings,
        "case_evidence_ids": [c["document_id"] for c in cases],
        "technical_reference_ids": [d["document_id"] for d in references],
        "additional_questions": questions,
        "inspection_proposals": proposals,
        "unknown_labels": {"pcb": pcb["unknown_labels"], "damage": damage["unknown_labels"]},
        "severity": "U",
        "severity_reason": "현재 요청에는 심각도를 확정할 검증된 치수·회로·기능 시험 결과가 없습니다.",
        "diagnosis_confirmed": False,
        "requires_human_approval": True,
    }
