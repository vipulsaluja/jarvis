import argparse
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from agent.system_prompt import SYSTEM_PROMPT
from memory.loader import load_static_memory
from memory.router.entity_detector import detect_entities
from memory.router.entity_loader import load_entities

_SEMANTIC_DIR = Path(__file__).parent.parent / "memory" / "semantic"
_CONFIDENCE_THRESHOLD = 0.7


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

def _build_system_prompt() -> str:
    static = load_static_memory()
    if static:
        return SYSTEM_PROMPT.rstrip() + "\n\n" + static
    return SYSTEM_PROMPT


def _prepend_entity_context(message: str, verbose: bool) -> str:
    paths = detect_entities(message)
    if not paths:
        return message
    context = load_entities(paths)
    if not context:
        return message
    if verbose:
        names = [p.stem for p in paths]
        print(f"[memory] loaded entities: {', '.join(names)}", file=sys.stderr)
    return f"{context}\n\n---\n{message}"


def chat(message: str, session_id: str, is_first: bool, system_prompt: str = "") -> str:
    if is_first:
        cmd = [
            "claude", "-p",
            "--session-id", session_id,
            "--system-prompt", system_prompt,
            "--permission-mode", "bypassPermissions",
            message,
        ]
    else:
        cmd = [
            "claude", "-p",
            "--resume", session_id,
            "--permission-mode", "bypassPermissions",
            message,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return f"[Error: {result.stderr.strip()}]"
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Remember
# ---------------------------------------------------------------------------

def _parse_fact(fact: str) -> dict:
    prompt = (
        'Parse this fact into JSON with exactly these fields: '
        'entity_type ("person", "project", or "preference"), '
        'entity_name (lowercase with underscores, no spaces), '
        'fact_key (lowercase with underscores, descriptive), '
        'fact_value (the fact as a clean phrase or sentence). '
        f'Fact: "{fact}"\n'
        'Return only valid JSON, no explanation, no markdown fences.'
    )
    result = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Claude parse failed: {result.stderr.strip()}")
    raw = result.stdout.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = "\n".join(
            line for line in raw.splitlines()
            if not line.strip().startswith("```")
        )
    return json.loads(raw.strip())


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


def _prompt(msg: str, default_yes: bool = True) -> bool:
    hint = "[Y/n]" if default_yes else "[y/N]"
    try:
        answer = input(f"{msg} {hint} ").strip().lower()
    except EOFError:
        return default_yes
    if not answer:
        return default_yes
    return answer == "y"


def _remember(fact: str) -> None:
    print(f"Parsing: {fact!r}")
    parsed = _parse_fact(fact)

    entity_type = parsed.get("entity_type", "preference")
    entity_name = parsed.get("entity_name", "unknown")
    fact_key = parsed.get("fact_key", "note")
    fact_value = parsed.get("fact_value", fact)

    path = _entity_path(entity_type, entity_name)
    data = _load_entity(path, entity_type, entity_name)
    facts = data.setdefault("facts", {})

    # Always show what was parsed and existing entity facts so the user can
    # catch key-mismatch conflicts (Claude's key names are non-deterministic).
    print(f"  entity : {entity_type} '{entity_name}'")
    print(f"  key    : {fact_key}")
    print(f"  value  : {fact_value}")
    if facts:
        print("  existing facts:")
        for k, v in facts.items():
            print(f"    {k} = '{v['value']}'")

    # If there are existing facts under different keys, let the user redirect
    # the write to replace one of them instead of creating a duplicate.
    other_keys = [k for k in facts if k != fact_key]
    if other_keys:
        print(f"  (will add as new key '{fact_key}'; enter an existing key to replace instead, or blank to continue)")
        try:
            override = input("  replace key: ").strip()
        except EOFError:
            override = ""
        if override:
            if override not in facts:
                print(f"Key '{override}' not found. Aborted.")
                return
            fact_key = override

    if not _prompt("Save?"):
        print("Aborted.")
        return

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    new_fact = {"value": fact_value, "confidence": 0.9, "updated": now, "source": "user-cli"}

    if fact_key in facts:
        existing = facts[fact_key]
        if existing.get("confidence", 0) < _CONFIDENCE_THRESHOLD:
            print(
                f"[memory] overwriting low-confidence fact: {fact_key} = '{existing['value']}'",
                file=sys.stderr,
            )

    facts[fact_key] = new_fact
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Saved: {entity_type} '{entity_name}' / {fact_key} = '{fact_value}'")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(prog="jarvis")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print memory debug info to stderr")
    subparsers = parser.add_subparsers(dest="command")

    remember_p = subparsers.add_parser("remember", help="Store a fact in semantic memory")
    remember_p.add_argument("fact", help='Natural-language fact, e.g. "Priya prefers async comms"')

    args = parser.parse_args()

    if args.command == "remember":
        _remember(args.fact)
        return

    session_id = str(uuid.uuid4())
    system_prompt = _build_system_prompt()
    is_first = True
    verbose = args.verbose
    print("Jarvis  (type 'quit' or 'exit' to stop)\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            break

        augmented = _prepend_entity_context(user_input, verbose)
        reply = chat(augmented, session_id, is_first, system_prompt)
        is_first = False
        print(f"\nJarvis: {reply}\n")


if __name__ == "__main__":
    main()
