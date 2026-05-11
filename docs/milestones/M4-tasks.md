# M4 — Episodic Memory: Task Breakdown

## Progress
- [ ] = pending  [~] = in progress  [x] = done

## Tasks

- [x] T1: Set up SQLite + sqlite-vec and define episode schema
  `memory/stores/episodic.py` exists with a `EpisodicStore` class that creates (on init) a SQLite DB at `memory/episodic.db` with the episode table: `{ id, timestamp, summary, embedding BLOB, entities TEXT (JSON array), importance REAL, access_count INTEGER }`. sqlite-vec is installed and the vector index is created. A `pytest` test or a simple `python -c` smoke test confirms the table is created and a row can be inserted and retrieved.

- [x] T2: Implement episode write path (summary + embedding)
  `EpisodicStore.add_episode(summary, entities, importance)` stores a row with a text embedding of the summary. Decide and document the embedding approach (OpenAI `text-embedding-3-small` or `sentence-transformers`) in a comment at the top of the file. The embedding is stored as a BLOB. Call this manually with a fake summary to confirm it round-trips.

- [x] T3: Implement episode read path (cosine similarity search)
  `EpisodicStore.search(query, top_k=3)` embeds the query and returns the top-k episodes ranked by cosine similarity, with a recency boost applied (e.g., multiply score by `1 + 0.1 * recency_factor`). Returns a list of `{ summary, entities, importance, timestamp }` dicts. Increment `access_count` for each returned episode.

- [ ] T4: Implement importance scoring at write time
  A standalone function `score_importance(summary: str) -> float` in `memory/stores/episodic.py` (or a shared utils file) returns a float 0.0–1.0. Rules: if summary contains decision/commitment keywords ("decided", "agreed", "will", "committed", "promised") → score >= 0.7. Small-talk patterns ("chatted", "mentioned", "asked about") → score <= 0.3. Write a brief docstring listing the keyword rules so they're auditable without reading the code.

- [ ] T5: Wire episodic retrieval into the agent context
  `agent/jarvis.py` calls `EpisodicStore.search(query)` on each user message and injects the top-k summaries into the system context under a `## Recent Episodes` section, within the 600-token budget defined in CLAUDE.md. If `--verbose`, print retrieved episodes to stderr. Injected text is trimmed to fit budget.

- [ ] T6: Implement post-conversation episode write
  After the conversation loop exits (user types "exit" or Ctrl-C), `jarvis.py` calls a `write_episode(conversation_history)` function that: (1) generates a 2-3 sentence summary of the conversation using a `claude -p` call, (2) extracts entity names mentioned using `detect_entities` from M3, (3) scores importance, (4) writes to the episodic store. If the importance score is below 0.2, skip the write. Print "Episode saved." or "Episode skipped (low importance)." to stderr.

- [ ] T7: End-to-end smoke test
  Have a conversation with Jarvis that includes a clear decision (e.g., "Let's use PostgreSQL for the auth service"). Exit. Start a new session and ask "what did we decide about the auth service?" — confirm the episodic summary appears in the response. Then have a trivial small-talk session and confirm no episode is written (or a low-importance one is skipped).
