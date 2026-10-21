import re
from .config import read_json

SURFACE_DEFECTS = {
    "crazing": ("잔금", "표면에 가는 균열이 여러 갈래로 보이는 후보"),
    "inclusion": ("이물 박힘", "표면에 이물이 박히거나 포함된 것처럼 보이는 후보"),
    "patches": ("얼룩·녹", "표면의 얼룩·변색 또는 녹처럼 보이는 후보"),
    "pitted_surface": ("패임", "표면에 작은 홈이나 패임이 보이는 후보"),
    "rolled-in_scale": ("압연 스케일", "금속 표면의 압연 스케일처럼 보이는 후보"),
    "scratches": ("긁힘", "표면에 선 모양의 긁힘이 보이는 후보"),
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


def interpret_damage_labels(labels: list[str]) -> dict:
    """Interpret surface-defect labels without inventing a product part or location."""
    known, unknown, seen = [], [], set()
    lookup = {key(label): label for label in SURFACE_DEFECTS}
    for raw in labels:
        label = lookup.get(key(raw))
        if label is None:
            unknown.append(raw)
            continue
        if label in seen:
            continue
        seen.add(label)
        name_ko, description_ko = SURFACE_DEFECTS[label]
        known.append({"raw_label": raw, "label": label, "name_ko": name_ko,
                      "description_ko": description_ko, "location": None,
                      "target_component": None,
                      "document_id": f"damage-label:surface:{label}",
                      "source": "team_damage_model_output", "diagnosis_confirmed": False})
    return {"detections": known, "unknown_labels": unknown,
            "input_state": "labels_received" if labels else "no_labels_provided",
            "scope": "Six surface-defect labels only. Coordinates are not processed; product part, material, severity and fault cause remain unverified."}
