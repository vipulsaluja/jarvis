# M7 — Prospective Memory: Task Breakdown

## Progress
- [ ] = pending  [~] = in progress  [x] = done

## Tasks

- [x] T1: Create ProspectiveStore SQLite class
  `memory/stores/prospective.py` with a `ProspectiveStore` class backed by SQLite. Schema: `id` (UUID), `content`, `due_date` (ISO-8601 string or NULL), `trigger_condition` (text or NULL), `status` (pending/done), `source_episode` (text or NULL), `created_at`. Methods: `add(content, due_date=None, trigger_condition=None, source_episode=None) -> str` (returns id), `get_due(as_of: str) -> list[dict]` (status=pending, due_date <= as_of), `get_condition_triggered(keywords: list[str]) -> list[dict]` (status=pending, any keyword in trigger_condition), `complete(id: str) -> None`, `list_pending() -> list[dict]`. DB file at `memory/prospective.db`.

- [x] T2: Natural-language date resolver
  A function `resolve_due_date(hint: str, today: str) -> str | None` in `pipeline/date_parser.py` that uses `claude -p` to convert hints like "next Friday", "tomorrow", "end of week" into ISO-8601 date strings (YYYY-MM-DD). Pass `today` as context so Claude can anchor the resolution. Returns None if hint is None or cannot be resolved. Verify: "next Friday" from 2026-05-11 → "2026-05-15"; None → None.

- [x] T3: Persist commitments into ProspectiveStore
  Update `run_post_conversation_pipeline` in `pipeline/extractor.py` to persist each commitment from `extract_commitments` into `ProspectiveStore`. For each commitment: call `resolve_due_date(due_date_hint, today)` to get an ISO date (or None); call `store.add(content, due_date=resolved, trigger_condition=None)`. Log each persist to stderr as `[write] commitment persisted: {content}`. Also write a `_log("commitment", ...)` entry. Verify: after a conversation with "remind me to follow up next week", `ProspectiveStore().list_pending()` returns one entry with a non-null due_date.

- [x] T4: Session-start prospective briefing
  In `main()` in `agent/jarvis.py`, before the conversation loop, instantiate `ProspectiveStore` and call `get_due(today_iso)`. If any items are returned, print a formatted briefing block to stdout before the first prompt — e.g. `"--- Reminders ---\n• {content} (due {due_date})\n---\n"`. Also call `list_pending()` to surface condition-triggered items that have no due_date but a trigger_condition — these will be checked per-turn in T5. Done when: starting a new session after a commitment was logged shows the reminder before "You:".

- [x] T5: Condition-triggered prospective checks during conversation
  In the conversation loop in `main()`, after each user message, extract keywords (split on whitespace, lowercase, deduplicate) and call `ProspectiveStore().get_condition_triggered(keywords)`. If any matches, print them inline to stdout as `"[reminder] {content}"` and do NOT complete them automatically (user must confirm). Done when: saying "what's the status of the release?" surfaces a pending item with trigger_condition containing "release".

- [x] T6: End-to-end smoke test
  Run a conversation that says "remind me to follow up with Rachita next week" and exit. Confirm: (1) `ProspectiveStore().list_pending()` has the entry with a resolved due_date; (2) `memory/write_log.jsonl` has a commitment line; (3) starting a new session within the due window prints the reminder briefing before the prompt. Run a second conversation with no commitments and confirm no spurious briefing appears.
