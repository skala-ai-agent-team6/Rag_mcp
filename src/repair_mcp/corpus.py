"""Source documents stay separate from model label definitions."""
import json
import re
from .config import DATA, read_json
from .labels import DAMAGE_PARTS


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


def damage_definitions() -> list[dict]:
    return [{
        "document_id": f"damage-label:{kind}:{part}",
        "source_type": "team_label_definition",
        "source": "Team-provided model class list",
        "product_domain": "automotive",
        "damage_type": kind, "part": part, "part_ko": korean,
        "text": f"{kind}: {part} — {korean} " + ("파손" if kind == "damage" else "찌그러짐") +
                ". 자동차 부위 분류 라벨이다. 실제 고장 원인이나 로봇청소기의 대응 부위를 확정하지 않는다.",
        "applicability": "Automotive model label definition, not a confirmed repair case.",
    } for kind, parts in DAMAGE_PARTS.items() for part, korean in parts.items()]
