from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from pipeline.write_log import append as _log
from pipeline.date_parser import resolve_due_date
from memory.stores.prospective import ProspectiveStore

_SEMANTIC_DIR = Path(__file__).parent.parent / "memory" / "semantic"

_EXTRACT_PROMPT = """\
Analyze this conversation and extract two kinds of information:

1. ENTITY FACTS — factual statements about named people or named projects.
   Examples: "Rachita is a manager", "the Jarvis project uses SQLite".

2. USER PREFERENCES — statements where the user expresses a preference, habit, or standing instruction.
   Look for patterns like: "I prefer", "I like", "I always", "I never", "I usually", "I don't like", "I want".
   Examples: "I prefer morning meetings", "I always review PRs before merging".

Return a JSON array of objects. Each object must have exactly these fields:
- entity_type: "person", "project", or "preference"
- entity_name: lowercase with underscores (e.g. "rachita", "jarvis_project"); for preferences always use "user"
- fact_key: lowercase with underscores, descriptive (e.g. "role", "team", "prefers_morning_meetings")
- fact_value: the fact as a clean phrase or sentence
- confidence: 0.9 if explicitly stated, 0.6 if inferred

Only include facts clearly present in the conversation. Do not invent. If nothing qualifies, return [].

Conversation:
{conversation}

Return only valid JSON array, no explanation, no markdown fences."""


def _entity_path(entity_type: str, entity_name: str) -> Path:
    if entity_type == "person":
        return _SEMANTIC_DIR / "people" / f"{entity_name}.json"
    if entity_type == "project":
        return _SEMANTIC_DIR / "projects" / f"{entity_name}.json"
    return _SEMANTIC_DIR / "preferences.json"


def _load_entity(path: Path, entity_type: str, entity_name: str) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    if entity_type == "preference":
        return {"_schema": "General user preferences.", "facts": {}}
    display_name = entity_name.replace("_", " ").title()
    return {"name": display_name, "type": entity_type, "facts": {}}


def _upsert_fact(entity_type: str, entity_name: str, fact_key: str, fact_value: str, confidence: float) -> None:
    path = _entity_path(entity_type, entity_name)
    data = _load_entity(path, entity_type, entity_name)
    facts = data.setdefault("facts", {})

    existing = facts.get(fact_key)
    if existing and existing.get("confidence", 0) >= 0.8:
        if entity_type == "preference":
            print(f"[write] skipped high-confidence preference: {fact_key}", file=sys.stderr)
        else:
            print(f"[write] skipped high-confidence fact: {entity_name}/{fact_key}", file=sys.stderr)
        return

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    facts[fact_key] = {
        "value": fact_value,
        "confidence": confidence,
        "updated": now,
        "source": "auto-extract",
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    log_type = "preference" if entity_type == "preference" else "entity"
    _log(log_type, f"{entity_name}/{fact_key}", fact_value)
    print(f"[write] entity upserted: {entity_type} '{entity_name}' / {fact_key} = '{fact_value}' (confidence={confidence})", file=sys.stderr)


_COMMITMENT_PROMPT = """\
Analyze this conversation and identify commitment or decision statements made by the user.

Look for patterns like: "I will", "I'll", "we decided", "remind me", "let's do", "I'll follow up", \
"I'm going to", "we agreed", "I need to", "I should".

Return a JSON array of objects. Each object must have exactly these fields:
- content: the commitment or decision as a clean, self-contained sentence
- due_date_hint: a natural-language date/time string if mentioned (e.g. "next Friday", "tomorrow", \
"end of week"), or null if no time was specified

Only include genuine commitments or decisions — not casual observations. \
If nothing qualifies, return [].

Conversation:
{conversation}

Return only valid JSON array, no explanation, no markdown fences."""


def extract_commitments(conversation_history: list[dict]) -> list[dict]:
    if not conversation_history:
        return []

    turns = "\n".join(
        f"{t['role'].capitalize()}: {t['content']}" for t in conversation_history
    )
    prompt = _COMMITMENT_PROMPT.format(conversation=turns)

    result = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[write] commitment extraction failed: {result.stderr.strip()}", file=sys.stderr)
        return []

    raw = result.stdout.strip()
    if raw.startswith("```"):
        raw = "\n".join(
            line for line in raw.splitlines()
            if not line.strip().startswith("```")
        )

    try:
        commitments = json.loads(raw.strip())
    except json.JSONDecodeError as e:
        print(f"[write] commitment extraction JSON parse error: {e}", file=sys.stderr)
        return []

    if not isinstance(commitments, list):
        print("[write] commitment extraction returned non-list", file=sys.stderr)
        return []

    valid = []
    for item in commitments:
        content = item.get("content", "").strip()
        if not content:
            continue
        due_date_hint = item.get("due_date_hint") or None
        valid.append({"content": content, "due_date_hint": due_date_hint})
        _log("commitment", due_date_hint or "no-date", content)
        print(f"[write] commitment detected: {content}", file=sys.stderr)

    return valid


def _persist_commitments(commitments: list[dict], today: str) -> None:
    store = ProspectiveStore()
    for c in commitments:
        content = c["content"]
        hint = c.get("due_date_hint")
        due_date = resolve_due_date(hint, today) if hint else None
        item_id = store.add(content, due_date=due_date)
        _log("commitment", due_date or "no-date", content)
        print(f"[write] commitment persisted: {content}", file=sys.stderr)
    store.close()


def run_post_conversation_pipeline(conversation_history: list[dict], verbose: bool = False, today: str | None = None) -> None:
    if not conversation_history:
        return

    if today is None:
        today = datetime.now(timezone.utc).date().isoformat()

    if verbose:
        print("[pipeline] running post-conversation extraction...", file=sys.stderr)

    try:
        extract_and_upsert_entities(conversation_history)
    except Exception as e:
        print(f"[pipeline] entity extraction error: {e}", file=sys.stderr)

    try:
        commitments = extract_commitments(conversation_history)
        if commitments:
            if verbose:
                print(f"[pipeline] {len(commitments)} commitment(s) detected", file=sys.stderr)
            _persist_commitments(commitments, today)
    except Exception as e:
        print(f"[pipeline] commitment extraction error: {e}", file=sys.stderr)

    if verbose:
        print("[pipeline] post-conversation extraction complete", file=sys.stderr)


def extract_and_upsert_entities(conversation_history: list[dict]) -> None:
    if not conversation_history:
        return

    turns = "\n".join(
        f"{t['role'].capitalize()}: {t['content']}" for t in conversation_history
    )
    prompt = _EXTRACT_PROMPT.format(conversation=turns)

    result = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[write] entity extraction failed: {result.stderr.strip()}", file=sys.stderr)
        return

    raw = result.stdout.strip()
    if raw.startswith("```"):
        raw = "\n".join(
            line for line in raw.splitlines()
            if not line.strip().startswith("```")
        )

    try:
        facts = json.loads(raw.strip())
    except json.JSONDecodeError as e:
        print(f"[write] entity extraction JSON parse error: {e}", file=sys.stderr)
        return

    if not isinstance(facts, list):
        print("[write] entity extraction returned non-list", file=sys.stderr)
        return

    for item in facts:
        entity_type = item.get("entity_type", "")
        entity_name = item.get("entity_name", "")
        fact_key = item.get("fact_key", "")
        fact_value = item.get("fact_value", "")
        confidence = float(item.get("confidence", 0.6))

        if not all([entity_type, entity_name, fact_key, fact_value]):
            continue
        if entity_type not in {"person", "project", "preference"}:
            continue

        _upsert_fact(entity_type, entity_name, fact_key, fact_value, confidence)
