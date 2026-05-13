"""M6 end-to-end smoke test for the automated write path."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.extractor import run_post_conversation_pipeline

LOG_PATH = ROOT / "memory" / "write_log.jsonl"
RACHITA_PATH = ROOT / "memory" / "semantic" / "people" / "rachita.json"
PREFS_PATH = ROOT / "memory" / "semantic" / "preferences.json"


def _log_lines_since(offset: int) -> list[dict]:
    if not LOG_PATH.exists():
        return []
    lines = LOG_PATH.read_text().splitlines()
    return [json.loads(l) for l in lines[offset:] if l.strip()]


def run() -> bool:
    print("=== M6 Smoke Test ===\n")
    ok = True

    # --- Test 1: rich conversation ---
    log_offset = len(LOG_PATH.read_text().splitlines()) if LOG_PATH.exists() else 0

    rich_history = [
        {"role": "user",      "content": "Rachita is moving to a new team next month."},
        {"role": "assistant", "content": "Got it, I'll remember that."},
        {"role": "user",      "content": "I prefer morning meetings — never schedule me after 3pm."},
        {"role": "assistant", "content": "Noted."},
        {"role": "user",      "content": "Also, let's use Redis for caching in the new service."},
        {"role": "assistant", "content": "Redis it is."},
    ]

    print("[1] Running pipeline on rich conversation...")
    run_post_conversation_pipeline(rich_history, verbose=True)
    print()

    new_log = _log_lines_since(log_offset)

    # Check 1: Rachita entity updated
    rachita_ok = RACHITA_PATH.exists() and "team" in json.loads(RACHITA_PATH.read_text()).get("facts", {})
    print(f"  (1) Rachita entity updated:          {'PASS' if rachita_ok else 'FAIL'}")
    ok = ok and rachita_ok

    # Check 2: preferences.json has morning meeting entry
    prefs = json.loads(PREFS_PATH.read_text()).get("facts", {}) if PREFS_PATH.exists() else {}
    pref_ok = any("morning" in v.get("value", "").lower() for v in prefs.values())
    print(f"  (2) Morning meeting pref written:    {'PASS' if pref_ok else 'FAIL'}")
    ok = ok and pref_ok

    # Check 3: commitment logged to write_log
    commitment_ok = any(e["type"] == "commitment" for e in new_log)
    print(f"  (3) Commitment entry in write_log:   {'PASS' if commitment_ok else 'FAIL'}")
    ok = ok and commitment_ok

    # Check 4: write_log has entries for entity + preference + commitment
    types_written = {e["type"] for e in new_log}
    log_ok = {"entity", "commitment"}.issubset(types_written)
    print(f"  (4) write_log has entity+commitment: {'PASS' if log_ok else 'FAIL'}")
    print(f"      types seen: {sorted(types_written)}")
    ok = ok and log_ok

    print()

    # --- Test 2: trivial conversation writes nothing ---
    log_offset2 = len(LOG_PATH.read_text().splitlines()) if LOG_PATH.exists() else 0

    trivial_history = [
        {"role": "user",      "content": "What is 2 + 2?"},
        {"role": "assistant", "content": "4."},
    ]

    print("[2] Running pipeline on trivial conversation...")
    run_post_conversation_pipeline(trivial_history, verbose=False)

    new_log2 = _log_lines_since(log_offset2)
    trivial_ok = len(new_log2) == 0
    print(f"  (5) Trivial conversation writes nothing: {'PASS' if trivial_ok else 'FAIL'}")
    if new_log2:
        print(f"      unexpected entries: {new_log2}")
    ok = ok and trivial_ok

    print()
    print(f"=== Result: {'ALL PASS' if ok else 'SOME FAILURES'} ===")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
