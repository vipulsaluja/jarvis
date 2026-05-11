# M6 — Automated Write Path: Task Breakdown

## Progress
- [ ] = pending  [~] = in progress  [x] = done

## Tasks

- [ ] T1: Extract entities from conversation and upsert semantic memory
  A function `extract_and_upsert_entities(conversation_history: list[dict]) -> None` in `pipeline/extractor.py` makes a `claude -p` call that returns a JSON array of `{ entity_type, entity_name, fact_key, fact_value }` objects extracted from the conversation. For each, it upserts into the appropriate semantic entity file (people/, projects/, preferences.json) using the same write logic as `_remember()` in `jarvis.py` — but without prompting for confirmation, since this is automated. Low-confidence facts (inferred, not stated explicitly) are written with `confidence: 0.6`; explicitly stated facts get `confidence: 0.9`. A write log line is printed to stderr for each upserted fact.

- [ ] T2: Detect preference statements and update preferences.json
  Inside `extract_and_upsert_entities` (or as a separate pass), detect preference patterns ("I prefer", "I like", "I always", "I never", "I usually") in the conversation and write them to `memory/semantic/preferences.json` under descriptive keys. If the key already exists with confidence >= 0.8, skip the overwrite and log "skipped high-confidence preference: {key}". Verify by having a conversation that states a preference and confirming it appears in preferences.json afterward.

- [ ] T3: Detect commitments and decisions for prospective memory
  A function `extract_commitments(conversation_history: list[dict]) -> list[dict]` in `pipeline/extractor.py` uses a `claude -p` call to identify commitment/decision statements ("I will", "we decided", "remind me", "let's do", "I'll follow up"). Returns a list of `{ content, due_date_hint }` dicts — `due_date_hint` is a natural-language string like "next Friday" or None. These are returned to the caller (M7 will persist them; for now, just log them to stderr as "commitment detected: {content}").

- [ ] T4: Wire extraction pipeline into post-conversation job
  After the conversation loop exits in `jarvis.py`, the existing `_write_episode()` call is joined by `run_post_conversation_pipeline(history, verbose)` — a function in `pipeline/extractor.py` that runs T1–T3 in sequence. Each step is wrapped in a try/except so a failure in one doesn't block the others. If `--verbose`, print a summary of what was extracted and written. The pipeline runs synchronously for now (async in M8).

- [ ] T5: Implement write log for auditability
  A `pipeline/write_log.py` module appends one JSON line per write to `memory/write_log.jsonl`: `{ timestamp, type (entity/preference/commitment/episode), key, value, source_turn }`. The `EpisodicStore.add_episode` and all entity upserts from T1–T3 write a log entry. This is append-only — never modified. Verify by checking the file after a conversation that produces at least one write.

- [ ] T6: End-to-end automated write smoke test
  Have a conversation with Jarvis that includes: (a) a stated fact about a person ("Rachita is moving to a new team"), (b) a preference ("I prefer morning meetings"), (c) a decision ("let's use Redis for caching"). Exit. Confirm: (1) the entity file for Rachita is updated, (2) preferences.json has the morning meeting preference, (3) a commitment entry is logged to stderr, (4) `memory/write_log.jsonl` has entries for each write. Then have a trivial conversation and confirm the pipeline runs but writes nothing (or minimal content).
