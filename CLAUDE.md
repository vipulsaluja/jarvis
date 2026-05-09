# Jarvis — Project Context

## What This Is
A personal AI assistant with sophisticated memory management. The core differentiator is not voice or tool integrations — it's a tiered memory architecture that retrieves the right context for each query without ballooning token usage or diluting attention.

The goal: an agent that feels like it *knows* you, because it remembers correctly — not because it stores everything.

## Key Documents
- `docs/BEHAVIORAL_SPEC.md` — source of truth for persona, interaction model, memory policy, trust model. System prompt is derived from this.
- `docs/roadmap.md` — 12-milestone roadmap (M0–M11)

## Architecture Overview

### Memory Tiers
| Type | What | Storage | Always Loaded? |
|------|------|---------|----------------|
| Procedural | Standing instructions, habits | `memory/procedural.md` | Yes |
| Semantic (hot) | Key facts about user/world | `memory/semantic/hot.json` | Yes |
| Semantic (entities) | Facts about people/projects | `memory/semantic/{entity}.json` | On-demand |
| Episodic | What happened in past conversations | SQLite + vectors | Retrieved (top-k) |
| Prospective | Future intentions, reminders | SQLite | Time/condition triggered |
| Working | Current session context | In-context | Yes (sliding window) |

### Token Budget per Query
- System prompt + procedural: ~800 tokens
- Hot semantic: ~300 tokens
- Retrieved episodic summaries: ~600 tokens
- Entity facts (on-demand): ~300 tokens
- Working memory (conversation): remainder of context window

### Memory Router
A fast classifier (Claude Haiku) runs before every main Claude call. It tags the query with required memory types, then the composer assembles the context window within budget. The agent never manages its own context — the router does.

### Write Path (async, post-conversation)
Every conversation triggers a background job:
1. Entity extraction → upsert semantic memory
2. Significance scoring → write episode if threshold met
3. Commitment/decision detection → add to prospective memory
4. Preference detection → update `preferences.json`

Writes never block responses.

## Tech Stack
- **Language:** Python
- **LLM:** Claude API (`claude-sonnet-4-6` for main agent, `claude-haiku-4-5` for memory router/classifier)
- **Vector storage:** SQLite + sqlite-vec (local, no infra)
- **Embeddings:** To be decided (OpenAI `text-embedding-3-small` or local via `sentence-transformers`)
- **STT:** OpenAI Whisper (M10)
- **TTS:** ElevenLabs (M10)
- **Wake word:** Picovoice Porcupine (M11)

## Project Structure (target)
```
jarvis/
  agent/
    jarvis.py          # main loop
  memory/
    router/
      classifier.py    # query → memory types needed
      composer.py      # assemble context within token budget
      writer.py        # post-conversation memory extraction
    stores/
      episodic.py      # SQLite + vectors
      semantic.py      # JSON entity files
      prospective.py   # SQLite with triggers
    procedural.md      # always-loaded instructions
    semantic/
      hot.json         # always-loaded key facts
  pipeline/
    decay.py           # nightly summarization jobs
    extractor.py       # entity + fact extraction
  tools/               # tool definitions (calendar, slack, etc.)
  docs/
    BEHAVIORAL_SPEC.md
    roadmap.md
    milestones/
      M0-tasks.md    # created by /next when starting M0
      M1-tasks.md    # created by /next when starting M1
      ...
  .claude/
    skills/
      next/          # /next skill — resume work on current milestone
  CLAUDE.md
```

## How to Resume Work
Run `/next` at the start of any session. The skill will:
1. Read this file to find the current milestone
2. Create `docs/milestones/{milestone-id}-tasks.md` if it doesn't exist yet
3. Otherwise, find the first pending or in-progress task and start on it

After a `/clear`, just run `/next` again — task state is persisted in the milestone file.

## Current Milestone
**M0 — Behavioral Spec** (not started)
Next: draft `docs/BEHAVIORAL_SPEC.md` by working through persona, interaction model, memory policy, trust model, and scope boundaries.

## Design Principles
- **Retrieval over storage:** prefer smaller, well-indexed stores over comprehensive dumps
- **Async writes:** memory writes never block user-facing responses
- **Spec-driven:** system prompt and memory policies trace back to `BEHAVIORAL_SPEC.md`
- **Local-first:** sensitive memory stays on-device; API calls only where necessary
- **Each memory type has one job:** don't let episodic and semantic blur — episodic is *what happened*, semantic is *what's true*

## What NOT to Do
- Don't load all memory into every context — defeats the purpose of the router
- Don't store episodic memory as full conversation transcripts — store summaries + embeddings
- Don't build voice (M10) before memory is solid (M2–M6)
- Don't silently overwrite high-confidence semantic facts — flag for user confirmation
