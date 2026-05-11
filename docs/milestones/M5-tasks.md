# M5 — Memory Router: Task Breakdown

## Progress
- [ ] = pending  [~] = in progress  [x] = done

## Tasks

- [x] T1: Define memory type taxonomy and classifier contract
  A file `memory/router/classifier.py` exists with a `classify_query(query: str) -> list[str]` function stub. The return type is a list of memory type tags from a fixed set: `["procedural", "hot_semantic", "episodic", "entity", "prospective"]`. A module-level docstring documents what each tag means and what query patterns trigger it (e.g., "remember when" → episodic, named person → entity, time/date reference → prospective). The stub returns all tags by default until the real classifier is wired in.

- [x] T2: Implement Haiku-powered query classifier
  `classify_query` makes a `claude -p` call using `claude-haiku-4-5-20251001` (fast + cheap) with a tightly scoped prompt that returns a JSON array of tags. The prompt is deterministic and includes 5-6 few-shot examples covering the major patterns. Add a 2-second timeout and fall back to returning all tags on failure. Verify with 5 manual test queries that the classifier returns sensible, minimal tag sets.

- [x] T3: Implement token budget manager
  A file `memory/router/composer.py` exists with a `MemoryComposer` class. It holds budget constants matching CLAUDE.md: procedural=800, hot_semantic=300, episodic=600, entity=300. A `compose(query, tags, conversation_history) -> str` method assembles a system prompt string by loading only the memory types in `tags`, trimming each section to its budget using a character-count heuristic (1 token ≈ 4 chars). Returns the assembled system prompt.

- [x] T4: Entity mention detection → auto-load entity files
  Inside `compose()`, if `"entity"` is in tags, run a regex/string scan over the query to find names that match filenames in `memory/semantic/` (people/, projects/). Load matching entity JSON files and inject them under a `## Entity Context` section, within the 300-token budget. If no files match, skip the section silently. Test with a query mentioning a known entity name.

- [x] T5: Temporal reference detection → load prospective memories
  Inside `compose()`, if `"prospective"` is in tags, query the prospective memory store (from M7 — stub it with an empty list for now) and inject any due items under `## Upcoming`. For now, a simple date-keyword scan (`"today"`, `"tomorrow"`, `"this week"`, `"remind"`) in the query triggers the prospective tag in the classifier. This wires the detection path even before M7 is complete.

- [x] T6: Wire composer into the agent loop
  `agent/jarvis.py` is updated to call `classify_query(user_message)` on each user turn, then call `composer.compose(query, tags, conversation_history)` to build the system prompt dynamically. The old static system prompt construction is replaced. If `--verbose`, print the active tags and token budget breakdown to stderr. Existing episodic retrieval (M4) is now driven by whether `"episodic"` is in tags rather than always running.

- [x] T7: End-to-end routing smoke test
  Run three queries and confirm correct tag sets and context sections appear (via `--verbose`):
  1. "What's 2+2?" → only `procedural` + `hot_semantic` loaded, no episodic or entity sections
  2. "What do I know about Priya?" → `entity` tag fired, Priya's entity file injected
  3. "Remember when we discussed the auth refactor?" → `episodic` tag fired, episodic search runs
