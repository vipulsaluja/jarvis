from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_LOG_PATH = Path(__file__).parent.parent / "memory" / "write_log.jsonl"


def append(
    entry_type: str,
    key: str,
    value: str,
    source_turn: str | None = None,
) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "type": entry_type,
        "key": key,
        "value": value,
        "source_turn": source_turn,
    }
    try:
        with _LOG_PATH.open("a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        print(f"[write_log] failed to append: {e}", file=sys.stderr)
