from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from agent.system_prompt import SYSTEM_PROMPT

_MEMORY_DIR = Path(__file__).parent.parent
_CHARS_PER_TOKEN = 4

BUDGET_PROCEDURAL = 800
BUDGET_HOT_SEMANTIC = 300
BUDGET_EPISODIC = 600
BUDGET_ENTITY = 300


def _trim(text: str, token_budget: int) -> str:
    char_limit = token_budget * _CHARS_PER_TOKEN
    if len(text) <= char_limit:
        return text
    return text[:char_limit].rsplit("\n", 1)[0]


def _load_procedural() -> str:
    path = _MEMORY_DIR / "procedural.md"
    if not path.exists():
        return ""
    raw = path.read_text().strip()
    lines = [l for l in raw.splitlines() if not l.startswith("Standing instructions.") and not l.startswith("Keep this")]
    return _trim("\n".join(lines).strip(), BUDGET_PROCEDURAL)


def _load_hot_semantic() -> str:
    path = _MEMORY_DIR / "semantic" / "hot.json"
    if not path.exists():
        return ""
    hot = json.loads(path.read_text())
    hot.pop("_schema", None)
    if not hot:
        return ""

    lines = ["## About You"]
    if name := hot.get("name"):
        lines.append(f"- Name: {name}")
    if tz := hot.get("timezone"):
        lines.append(f"- Timezone: {tz}")
    if projects := hot.get("current_projects"):
        lines.append("- Current projects:")
        for p in projects:
            lines.append(f"  - {p}")
    if people := hot.get("key_people"):
        lines.append("- Key people:")
        for k, v in people.items():
            lines.append(f"  - {k}: {v}")
    return _trim("\n".join(lines), BUDGET_HOT_SEMANTIC)


def _load_episodic(query: str) -> str:
    try:
        from memory.stores.episodic import EpisodicStore
        store = EpisodicStore()
        episodes = store.search(query, top_k=3)
    except Exception:
        return ""
    if not episodes:
        return ""

    lines = ["## Recent Episodes"]
    used = len(lines[0]) + 1
    char_limit = BUDGET_EPISODIC * _CHARS_PER_TOKEN
    for ep in episodes:
        ts = datetime.fromtimestamp(ep["timestamp"]).strftime("%Y-%m-%d")
        line = f"- [{ts}] {ep['summary']}"
        if used + len(line) + 1 > char_limit:
            break
        lines.append(line)
        used += len(line) + 1

    if len(lines) == 1:
        return ""
    return "\n".join(lines)


def _load_entity(query: str) -> str:
    from memory.router.entity_detector import detect_entities
    from memory.router.entity_loader import load_entities
    paths = detect_entities(query)
    return _trim(load_entities(paths), BUDGET_ENTITY)


def _load_prospective() -> str:
    # Stub — returns empty until M7 implements the prospective store.
    # M7 will replace this with: ProspectiveStore().get_due_items()
    items: list[str] = []
    if not items:
        return ""
    lines = ["## Upcoming"]
    for item in items:
        lines.append(f"- {item}")
    return "\n".join(lines)


class MemoryComposer:
    def compose(self, query: str, tags: list[str], conversation_history: list[dict], verbose: bool = False) -> str:
        """Assemble a system prompt from the base prompt plus tagged memory sections."""
        sections: list[str] = []
        budget_log: dict[str, int] = {}

        if "procedural" in tags:
            text = _load_procedural()
            if text:
                sections.append(text)
                budget_log["procedural"] = len(text) // _CHARS_PER_TOKEN

        if "hot_semantic" in tags:
            text = _load_hot_semantic()
            if text:
                sections.append(text)
                budget_log["hot_semantic"] = len(text) // _CHARS_PER_TOKEN

        if "episodic" in tags:
            text = _load_episodic(query)
            if text:
                sections.append(text)
                budget_log["episodic"] = len(text) // _CHARS_PER_TOKEN

        if "entity" in tags:
            text = _load_entity(query)
            if text:
                sections.append(text)
                budget_log["entity"] = len(text) // _CHARS_PER_TOKEN

        if "prospective" in tags:
            text = _load_prospective()
            if text:
                sections.append(text)
                budget_log["prospective"] = len(text) // _CHARS_PER_TOKEN

        if verbose and budget_log:
            total = sum(budget_log.values())
            parts = ", ".join(f"{k}={v}" for k, v in budget_log.items())
            print(f"[memory] tags={tags}", file=sys.stderr)
            print(f"[memory] budget: {parts} | total~{total} tokens", file=sys.stderr)

        if not sections:
            return SYSTEM_PROMPT

        memory_block = "\n\n".join(sections)
        return SYSTEM_PROMPT.rstrip() + "\n\n" + memory_block
