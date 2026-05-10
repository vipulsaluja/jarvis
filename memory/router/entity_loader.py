import json
from pathlib import Path

_ENTITY_TOKEN_BUDGET = 300
_CHARS_PER_TOKEN = 4


def _format_entity(data: dict, path: Path) -> str:
    name = data.get("name", path.stem)
    entity_type = data.get("type", "entity")
    facts = data.get("facts", {})
    if not facts:
        return ""
    lines = [f"### {name} ({entity_type})"]
    for key, fact in facts.items():
        label = key.replace("_", " ")
        lines.append(f"- {label}: {fact['value']}")
    return "\n".join(lines)


def load_entities(paths: list[Path]) -> str:
    """Format entity files into a context block within the token budget."""
    if not paths:
        return ""

    budget_chars = _ENTITY_TOKEN_BUDGET * _CHARS_PER_TOKEN
    blocks: list[str] = []
    total = 0

    for path in paths:
        try:
            data = json.loads(path.read_text())
            data.pop("_schema", None)
            block = _format_entity(data, path)
            if not block:
                continue
            if total + len(block) > budget_chars:
                break
            blocks.append(block)
            total += len(block)
        except (json.JSONDecodeError, OSError):
            continue

    if not blocks:
        return ""
    return "## Entity Facts\n" + "\n\n".join(blocks)
