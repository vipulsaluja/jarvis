# M3 — Semantic Memory (Entity Store): Task Breakdown

## Progress
- [ ] = pending  [~] = in progress  [x] = done

## Tasks

- [x] T1: Create entity store directory structure and schema
  `memory/semantic/people/`, `memory/semantic/projects/`, and `memory/semantic/preferences.json` exist. A `_schema.md` file documents the entity format: `{ facts: { key: { value, confidence, updated, source } } }`. Confidence is a float 0.0–1.0; threshold for silent overwrite vs. flag-for-confirmation is 0.7.

- [ ] T2: Populate sample entity files
  Add at least two people files (e.g. `priya.json`, `alex.json`) and one project file with realistic facts. This proves the schema is usable and gives the entity loader something to work with before the CLI write command exists.

- [ ] T3: Build entity loader (`memory/stores/semantic.py`)
  A `load_entity(name)` function reads the right JSON file from the correct subdirectory and returns its facts dict. A `list_entities()` function returns all entity names by subdirectory. File-not-found returns `None` (no crash).

- [ ] T4: Wire entity detection into the agent
  Before the main Claude call, scan the user's message for entity name mentions (simple substring match against known entity names). Load matching entity files and inject their facts into the context window under a clearly labelled section. No router yet — just direct matching.

- [ ] T5: Build the `jarvis remember` CLI command
  `python -m agent.jarvis remember "<fact string>"` parses a natural-language fact (e.g. "Priya prefers async comms"), extracts entity name + key + value using a lightweight heuristic or a single Claude call, then writes/updates the entity file. Low-confidence facts (< 0.7) overwrite silently; high-confidence facts that already exist with a different value print a confirmation prompt before overwriting.

- [ ] T6: Implement conflict resolution on write
  In the `remember` write path, if an existing fact has confidence >= 0.7 and the new value differs, print the old value and ask the user to confirm before overwriting. Update `confidence`, `updated`, and `source` fields on every write.

- [ ] T7: Smoke test entity recall
  Run the agent and ask "what do I know about Priya?" — confirm it returns structured facts from her entity file. Use `jarvis remember` to add a new fact, then verify it appears in the next query. Confirm conflict resolution fires when updating a high-confidence fact.
