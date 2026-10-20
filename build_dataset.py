"""Build reviewable RAG source documents from an unchanged DustUp CSV snapshot.

Standard library only. No API, embedding, database write, or model inference.
"""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = "https://github.com/openrepair/data/blob/main/quests/vacuums/dustup.csv"

# Korean paraphrases of source records. None means the source does not specify it.
# Fields: source id, symptom, reported observations, action taken.
CURATION = [
    ("anstiftung_6772", "잠깐 움직이다가 멈춤", "내부와 장애물 감지 센서가 오염되어 장애물이 있는 것으로 잘못 감지", "내부와 센서 청소"),
    ("anstiftung_2856", "전원이 켜지지 않음", "모터 속도 제어 트라이액은 정상. 기판 냉납과 마이크로스위치 접점 오염 발견", "기판 재납땜 및 스위치 접점 청소"),
    ("rcint_31607", "모터가 시작한 후 잠시 뒤 정지", "배터리는 정상. 흡입구 플랩이 먼지와 오염으로 고착", "흡입구 플랩을 움직여 고착 해소"),
    ("rcint_21434", "F2 오류", "센서 세 개 중 하나가 약간 오염됨", "브러시로 센서 청소"),
    ("rcint_19834", "스위치 고장으로 접수", "기판의 납땜 연결이 떨어져 있음", "재납땜"),
    ("rcint_18011", "충전 접점의 간헐적 작동", "12V 소켓 단자 파손", "단자 재납땜"),
    ("rcint_10275", "전혀 작동하지 않음", "전원 스위치 연결 배선 단선", "배선 재납땜"),
    ("rcint_25599", "작동 중 꺼짐", None, "배터리 접점 청소"),
    ("rcint_19886", "전원이 들어오지 않음", None, "배터리 단자 청소"),
    ("anstiftung_2774", "전혀 작동하지 않음", "모터 저항 측정에서 이상. 고정자 코일 접촉부의 배선 단선 발견", "단선 부위를 납땜"),
    ("anstiftung_2455", "전원을 켜면 잠깐 움직이려다가 정지", "도통 점검에서 전원선 단절. 플러그에 그을음과 결함 발견", "플러그 교체"),
    ("anstiftung_2987", "로봇청소기의 소음과 흡입력 감소", "분해 후 내부의 큰 먼지 뭉치 발견", "먼지 제거 및 내부 청소"),
    ("anstiftung_3020", "로봇청소기가 작동하지 않음", "주 전원 스위치 이상", "스위치 분리, 청소 후 재장착"),
    ("anstiftung_4182", "모터가 회전하지 않음", "모터 브러시는 마모되지 않았으나 하나가 가이드에 걸려 접촉 불량", "브러시 가이드 복구"),
    ("anstiftung_6276", "높은 휘파람 소리와 흡입력 저하", "필터 결함으로 모터 내부에 먼지가 유입됨", "모터와 하우징 청소"),
    ("anstiftung_7192", None, "물에 젖은 모터 브러시가 가이드에서 움직이지 않음", "카본 브러시를 연마해 접촉 복구"),
    ("rcint_1073", "단락 현상으로 차단기가 내려감", "오염 기록", "접점과 기판 청소"),
    ("rcint_1080", "큰 소음", "공기 통로 오염", "특히 모터 입구의 공기 통로 청소"),
    ("rcint_11380", "작동 중 멈춤", "카본 브러시 주변 오염", "분해 후 청소"),
    ("rcint_11648", "모터 고장으로 접수", "모터 결함으로 기록", "고객이 주문한 새 모터 장착"),
    ("rcint_13350", "전원 버튼 부근에서 불꽃 발생", "카본 브러시 마모로 전기자 손상", "새 모터 주문 후 장착"),
    ("rcint_14448", None, "카본 브러시가 오염으로 고착", "브러시 고착 해소 및 청소"),
    ("rcint_17553", "전원이 켜지지 않음", "카본 브러시 이탈 가능성으로 기록. 심한 오염과 잘못된 먼지봉투·필터 사용", "브러시 재장착 및 청소"),
    ("rcint_17875", "작동하지 않음", "모터 케이블 연결이 느슨함", "케이블 단자 교체 후 재연결"),
    ("rcint_19745", "작동하지 않음", "속도 조절 기판의 부품 고장. 부품명은 미기재", "기판 주문 후 교체"),
    ("rcint_19756", "작동하지 않음", "카본 브러시 홀더 접촉 불량", "접촉부에 배선 납땜"),
    ("rcint_22998", "시작·정지 버튼이 작동하지 않음", "카본 브러시 오염", "접점 세정제로 브러시 청소"),
    ("rcint_23473", "전원이 켜지지 않음", "카본 브러시 접촉 불량", "접점 세정제로 브러시 청소"),
    ("rcint_25741", "작동하지 않음", "모터 부근 속도 제어 기판의 사이리스터/트라이액 접촉 불량", "사이리스터/트라이액 재납땜"),
    ("rcint_32214", "흡입이 안 되는 것으로 접수", "흡입 자체는 문제없음. 브러시 축 구동 벨트가 모터 축에서 이탈하고 브러시 축 끝에 털 축적", "벨트 재장착, 털 제거 후 재조립"),
]


def main():
    raw = ROOT / "data/raw/dustup.csv"
    with raw.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    by_id = {row["id_ords"]: row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("Duplicate IDs in source")
    digest = hashlib.sha256(raw.read_bytes()).hexdigest()
    out = ROOT / "data/repair_cases"
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for source_id, symptom, observation, action in CURATION:
        r = by_id[source_id]
        if r["repair_status"] != "Fixed" or r["fault_type"] == "Poor data":
            raise ValueError(f"Unexpected source status for {source_id}")
        search = "\n".join(v for v in [
            f"제품: {r['brand']} 청소기",
            f"증상: {symptom}" if symptom else None,
            f"점검 기록: {observation}" if observation else None,
        ] if v)
        records.append({
            "document_id": f"dustup:{source_id}",
            "collection": "repair_cases",
            "source_type": "external_community_repair_record",
            "source_url": SOURCE,
            "source_id": source_id,
            "source_sha256": digest,
            "license": "CC-BY-SA-4.0",
            "attribution": "Open Repair Alliance / DustUp; provider: " + r["data_provider"],
            "review_status": "pending_team_review",
            "transformation": "AI-assisted Korean paraphrase; original text retained; not manufacturer-verified",
            "product_category": r["product_category"],
            "brand": None if r["brand"] == "Unknown" else r["brand"],
            "model_code": None,
            "reported_symptom_ko": symptom,
            "reported_observations_ko": observation,
            "reported_action_ko": action,
            "source_repair_status": r["repair_status"],
            "source_fault_type": r["fault_type"],
            "fault_type_provenance": "post-hoc community annotation; not a new technician diagnosis",
            "error_codes": ["F2"] if source_id == "rcint_21434" else [],
            "pcb_detections": None,
            "photos": [],
            "original_text": r["problem"],
            "event_date": r["event_date"],
            "search_text": search,
        })
    (out / "cases.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    lines = ["# 실제 수리 사례 검토 목록", "", "원본: Open Repair Alliance DustUp / CC BY-SA 4.0. 한국어 내용은 AI 보조 요약으로 팀 검토 전입니다.", "", "Fixed는 원본에 기록된 수리 결과입니다. 측정·제조사 검증을 새로 수행한 것이 아닙니다.", ""]
    for r in records:
        lines.extend([f"## {r['source_id']} · {r['brand'] or '브랜드 미상'}", "", r["search_text"], "", f"기록된 조치: {r['reported_action_ko']}", "", f"원본 결과: {r['source_repair_status']}", "", f"원문: {r['original_text']}", "", f"[원본 CSV]({SOURCE}) — 원본 ID로 찾기", ""])
    (out / "review.md").write_text("\n".join(lines), encoding="utf-8")
    # Broad corpus with original outcomes. This is coarse filtering, not verification.
    translations = {r["source_id"]: r for r in records}
    corpus, excluded = [], []
    for r in rows:
        reason = ("source_labeled_poor_data" if r["fault_type"] == "Poor data"
                  else "empty_problem" if not r["problem"].strip() else None)
        if reason:
            excluded.append({"source_id": r["id_ords"], "reason": reason})
            continue
        translated = translations.get(r["id_ords"])
        corpus.append({
            "document_id": f"dustup:{r['id_ords']}",
            "collection": "repair_cases",
            "source_type": "external_community_repair_record",
            "source_id": r["id_ords"],
            "source_url": SOURCE,
            "source_sha256": digest,
            "license": "CC-BY-SA-4.0",
            "attribution": "Open Repair Alliance / DustUp; provider: " + r["data_provider"],
            "brand": None if r["brand"] == "Unknown" else r["brand"],
            "product_category": r["product_category"],
            "model_code": None,
            "original_text": r["problem"],
            "search_text": r["problem"],
            "search_text_scope": "unstructured source record; may mix symptom, observations and actions",
            "korean_summary": ({k: translated[k] for k in (
                "reported_symptom_ko", "reported_observations_ko", "reported_action_ko"
            )} if translated else None),
            "source_repair_status": r["repair_status"],
            "source_fault_type": r["fault_type"],
            "source_repair_barrier": r["repair_barrier_if_end_of_life"] or None,
            "event_date": r["event_date"],
            "quality_screen": "nonempty_problem_and_not_source_poor_data",
            "review_status": "not_individually_verified",
            "pcb_detections": None,
        })
    (out / "all_cases.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in corpus), encoding="utf-8")
    (out / "excluded.json").write_text(json.dumps(excluded, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {"source_url": SOURCE, "retrieved_on": "2026-10-20", "sha256": digest, "source_rows": len(rows), "selected_rows": len(records), "license": "CC-BY-SA-4.0", "selection": "30 records selected for stated observations/actions; Fixed; excludes Poor data. Not a random sample.", "not_present_in_source": ["structured YOLO detections", "per-case photo links", "reliable model_code"], "embedding_executed": False}
    manifest.update({"corpus_rows": len(corpus), "excluded_rows": len(excluded),
                     "corpus_outcomes": dict(Counter(r["source_repair_status"] for r in corpus)),
                     "corpus_policy": "All outcomes; exclude source Poor data and empty problem only. Remaining rows are not individually verified."})
    (ROOT / "data/source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_rows": len(rows), "sample_rows": len(records), "corpus_rows": len(corpus), "excluded_rows": len(excluded), "outcomes": manifest["corpus_outcomes"], "output": str(out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
