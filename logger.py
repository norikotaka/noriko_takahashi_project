"""Development-only JSONL logger. Not durable on Streamlit Community Cloud."""
import json
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"


def log_event(participant_id, condition, event, **details):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": datetime.now(timezone.utc).isoformat(),
              "participant_id": participant_id, "condition": condition,
              "event": event, **details}
    with (LOG_DIR / f"{participant_id}.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record
