# M1 — Bare Agent Loop: Task Breakdown

## Progress
- [ ] = pending  [~] = in progress  [x] = done

## Tasks

- [x] T1: Python project scaffold
  `pyproject.toml` (or `requirements.txt`), `agent/`, `tools/`, `memory/` directories created. `python -m jarvis` or `python agent/jarvis.py` can be invoked without import errors. `.gitignore` covers Python artifacts.

- [x] T2: Distill system prompt from BEHAVIORAL_SPEC.md
  `agent/system_prompt.py` exists with a `SYSTEM_PROMPT` string constant that captures persona, response style, clarification policy, confirmation gates, and scope limits — tight enough for an LLM to follow, not a copy-paste of the full spec. Reading this file alone should be enough to understand how Jarvis should behave.

- [x] T3: Single-turn Claude Code CLI round-trip
  `agent/jarvis.py` sends one user message with the system prompt and prints the response via `claude -p --system-prompt`. Running it directly produces a real response.

- [x] T4: Multi-turn conversation loop
  The agent maintains a message history list for the session. Input loop runs until the user types `quit` or `exit`. Each turn appends to history so the model has full conversation context. "Hello Jarvis" followed by a follow-up question works correctly.

- [x] T5: Add 2-3 hardcoded tools with execution loop
  Tool definitions for `get_current_time` and `open_url` (plus optionally `get_weather_stub`) added to `tools/`. Agent delegates tool execution to the Claude Code CLI, which handles tool use natively. Asking "what time is it?" triggers the tool end-to-end.

- [x] T6: Smoke test end-to-end
  Run the full CLI manually. Confirm: multi-turn conversation holds context, tool calls work, responses are terse (no filler), and the agent asks before acting on an ambiguous request. Any behavior gaps from the spec are noted.
