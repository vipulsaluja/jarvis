# M2 — Procedural + Hot Semantic Memory: Task Breakdown

## Progress
- [ ] = pending  [~] = in progress  [x] = done

## Tasks

- [x] T1: Create memory directory structure and schema docs
  `memory/procedural.md` and `memory/semantic/hot.json` paths exist. A short schema comment in `hot.json` documents the expected fields (name, timezone, current_projects, key_people). No functional code yet — just the files in the right place.

- [x] T2: Populate procedural.md with standing instructions
  `memory/procedural.md` contains real, opinionated content: response style preferences, recurring habits, how Jarvis should address you, what it should never do unprompted. Content must be under 500 tokens (leaving headroom for hot.json).

- [x] T3: Populate hot.json with key facts
  `memory/semantic/hot.json` contains actual values: your name, timezone, 2-3 current projects, 3-5 key people. Total file under 300 tokens. Fields are stable and won't change conversation-to-conversation.

- [x] T4: Wire both files into the agent at startup
  `agent/jarvis.py` loads `procedural.md` and `hot.json` at startup and injects them into the system prompt (or as the first system turn). The agent sees this context on every turn without the user providing it.

- [x] T5: Enforce the 800-token combined budget
  At load time, count tokens for procedural + hot combined. If they exceed 800 tokens, print a warning to stderr (don't crash). Use a character-based estimate (~4 chars/token) — no SDK dependency needed since all LLM calls go through the Claude Code CLI.

- [x] T6: Smoke test personalization
  Run the agent cold. Confirm: it addresses you by name without being told, response style matches procedural instructions, and asking "what projects am I working on?" returns the hot.json values. Note any gaps.
