import json
import sys
from pathlib import Path

_MEMORY_DIR = Path(__file__).parent
_BUDGET_TOKENS = 800
_CHARS_PER_TOKEN = 4


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN)


def _format_hot(hot: dict) -> str:
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
        for person, desc in people.items():
            lines.append(f"  - {person}: {desc}")
    return "\n".join(lines)


def load_static_memory() -> str:
    """Load procedural.md and hot.json, return as a formatted string for injection into the system prompt."""
    parts = []

    procedural_path = _MEMORY_DIR / "procedural.md"
    if procedural_path.exists():
        raw = procedural_path.read_text().strip()
        # Strip the file's own header comment lines
        lines = [l for l in raw.splitlines() if not l.startswith("Standing instructions.") and not l.startswith("Keep this")]
        parts.append("\n".join(lines).strip())

    hot_path = _MEMORY_DIR / "semantic" / "hot.json"
    if hot_path.exists():
        hot = json.loads(hot_path.read_text())
        hot.pop("_schema", None)
        if hot:
            parts.append(_format_hot(hot))

    if not parts:
        return ""

    combined = "\n\n".join(parts)
    tokens = _estimate_tokens(combined)
    if tokens > _BUDGET_TOKENS:
        print(
            f"[memory] warning: static memory is ~{tokens} tokens, exceeds budget of {_BUDGET_TOKENS}",
            file=sys.stderr,
        )
    return combined
