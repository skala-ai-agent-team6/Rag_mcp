import json
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=False)
DATA = Path(os.environ.get("REPAIR_DATA_DIR", ROOT / "data")).resolve()
RUNTIME = Path(os.environ.get("REPAIR_RUNTIME_DIR", ROOT / ".runtime")).resolve()


def read_json(relative: str):
    return json.loads((DATA / relative).read_text(encoding="utf-8"))
