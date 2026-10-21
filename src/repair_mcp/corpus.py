"""Source documents stay separate from model label definitions."""
import json
import re
from .config import DATA, read_json


def load_documents() -> dict[str, list[dict]]:
    cases = [json.loads(line) for line in
             (DATA / "repair_cases/all_cases.jsonl").read_text().splitlines() if line.strip()]
    for case in cases:
        case["text"] = case["search_text"]
        case["product_domain"] = "vacuum"
    pcb = []
    for path in sorted((DATA / "pcb_documents").rglob("*.md")):
        text = path.read_text()
        match = re.search(r"문서 ID:\s*(\S+)", text)
        pcb.append({
            "document_id": match.group(1) if match else f"pcb-guide:{path.stem}",
            "title": text.splitlines()[0].lstrip("# "),
            "text": text, "source_path": str(path.relative_to(DATA)),
            "source_type": "team_label_definition" if path.parent.name == "labels" else "technical_reference",
            "source_urls": re.findall(r"https?://[^\s)]+", text),
            "applicability": "Reference only; product and circuit compatibility must be checked.",
        })
    damage = read_json("damage_documents/labels.json")
    return {"repair_cases": cases, "pcb_documents": pcb, "damage_documents": damage}
