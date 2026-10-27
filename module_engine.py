"""Load the original demo curriculum (never real research materials)."""
import json
from pathlib import Path


def load_module():
    path = Path(__file__).resolve().parent / "modules" / "module_1.json"
    return json.loads(path.read_text(encoding="utf-8"))
