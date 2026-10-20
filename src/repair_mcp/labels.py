import re
from .config import read_json
from .models import DamageLabel

DAMAGE_PARTS = {
    "damage": {
        "Front-windscreen": "앞유리", "Headlight": "전조등",
        "Rear-windscreen": "뒷유리", "Runningboard": "사이드 발판",
        "Sidemirror": "사이드미러", "Taillight": "후미등",
    },
    "dent": {
        "bonnet": "보닛", "boot": "트렁크", "doorouter": "도어 외판",
        "fender": "펜더", "front-bumper": "앞범퍼", "quaterpanel": "쿼터 패널",
        "rear-bumper": "뒷범퍼", "roof": "지붕",
    },
}


def key(value: str) -> str:
    return re.sub(r"[\s_-]+", "", value.strip().lower())


def interpret_pcb_labels(labels: list[str]) -> dict:
    """Interpret existing model labels; does not execute an image model."""
    taxonomy = read_json("pcb_label_taxonomy.json")["labels"]
    lookup = {key(alias): entry for entry in taxonomy
              for alias in [entry["label"], *entry["aliases"]]}
    known, unknown, seen = [], [], set()
    for raw in labels:
        entry = lookup.get(key(raw))
        if entry is None:
            unknown.append(raw)
        elif entry["label"] not in seen:
            seen.add(entry["label"])
            known.append({"raw_label": raw, "label": entry["label"],
                          "description_ko": entry["description_ko"],
                          "document_id": "pcb-label:" + entry["label"],
                          "source": "team_pcb_model_output", "diagnosis_confirmed": False})
    return {"detections": known, "unknown_labels": unknown,
            "input_state": "labels_received" if labels else "no_labels_provided",
            "scope": "Label interpretation only; an empty list does not certify a normal PCB."}


def interpret_damage_labels(labels: list[DamageLabel]) -> dict:
    """Keep automotive part labels and their damage type; no vacuum-part remapping."""
    known, unknown, seen = [], [], set()
    for item in labels:
        mapping = DAMAGE_PARTS[item.damage_type]
        lookup = {key(part): part for part in mapping}
        if item.damage_type == "dent":
            lookup[key("quarterpanel")] = "quaterpanel"  # preserve team's original spelling
        part = lookup.get(key(item.part))
        if part is None:
            unknown.append(item.model_dump())
            continue
        identity = (item.damage_type, part)
        if identity in seen:
            continue
        seen.add(identity)
        known.append({"raw_part": item.part, "part": part, "damage_type": item.damage_type,
                      "part_ko": mapping[part],
                      "description_ko": mapping[part] + (" 파손" if item.damage_type == "damage" else " 찌그러짐"),
                      "source_domain": "automotive",
                      "domain_compatible": False,
                      "document_id": f"damage-label:{item.damage_type}:{part}",
                      "source": "team_damage_model_output", "diagnosis_confirmed": False})
    return {"detections": known, "unknown_labels": unknown,
            "domain_mismatch": bool(known),
            "input_state": "labels_received" if labels else "no_labels_provided",
            "scope": "Automotive labels; vacuum component equivalence has not been established."}
