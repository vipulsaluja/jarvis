# M3 — Semantic Memory (Entity Store): Task Breakdown

## Progress
- [ ] = pending  [~] = in progress  [x] = done

## Tasks

- [x] T1: Create directory structure and schema definition
  `memory/semantic/people/`, `memory/semantic/projects/` directories exist. `memory/semantic/preferences.json` exists with an empty object `{}`. A `memory/semantic/SCHEMA.md` documents the entity schema: `{ facts: { key: { value, confidence, updated, source } } }` with field descriptions and valid confidence range (0.0–1.0).

- [x] T2: Populate initial entity files from existing knowledge
  Create at least one person entity file (e.g., `memory/semantic/people/priya.json`) and one project entity file using facts already in `hot.json`/`procedural.md`. Each file follows the schema. This validates the schema is workable and seeds Jarvis with real data.

- [x] T3: Implement entity detection (string matching, no LLM)
  `memory/router/entity_detector.py` exports a `detect_entities(query: str) -> list[Path]` function. It loads entity names from all files in `people/` and `projects/` and returns file paths for any names mentioned in the query. Pure string matching — fast, no API call.

- [x] T4: Wire entity loading into the agent context
  `agent/jarvis.py` calls `detect_entities()` on each user message and loads matched entity files into the system context (within the 300-token budget defined in the CLAUDE.md architecture). If `--verbose` flag is set, print which entities were loaded to stderr.

- [x] T5: Implement `jarvis remember` CLI command
  `python -m agent.jarvis remember "<fact>"` parses a natural-language fact string, infers entity type (person/project/preference) and entity name, then writes the key-value pair into the correct file with `confidence=0.5`, current timestamp as `updated`, and `source="user-cli"`. Duplicate keys in the same entity are merged, not appended.

- [x] T6: Implement conflict resolution on write
  When `remember` targets an existing fact key: if existing `confidence < 0.7`, overwrite silently and log to stderr. If existing `confidence >= 0.7`, print the existing fact and prompt `Overwrite? [y/N]` — do not write unless confirmed. New facts (no existing key) always write without prompting.

- [x] T7: End-to-end smoke test
  Run the agent and ask "what do you know about Priya?" — confirm entity facts appear in the response. Run `jarvis remember "Priya now prefers voice calls"` and re-ask — confirm the updated fact is reflected. Run remember twice with the same key — confirm no duplication.
