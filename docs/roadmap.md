# Jarvis — Project Roadmap

## North Star
A personal AI agent that feels like it *knows* you — because it remembers the right things, forgets the noise, and retrieves context intelligently without ballooning token usage.

---

## M0 — Behavioral Spec
**Goal:** Define what Jarvis *is* before writing a line of code. Every subsequent decision — system prompt, memory schema, tool permissions — derives from this.

### Persona
- Tone and address style: formal/informal, uses your name or not, humor threshold
- Response length default: terse or thorough? When does it elaborate vs. compress?
- Personality constraints: what makes it distinctly *yours* vs. generic assistant

### Interaction Model
- Clarification policy: does it ask before acting, or attempt + report?
- Confidence threshold: at what certainty does it say "I'm not sure" vs. just answer?
- Proactivity threshold: what warrants an unsolicited message? (meeting in 10 min = yes, new email = maybe, weather changed = no)
- Interruption policy: when always-on, what breaks through vs. stays queued?

### Memory Behavior
- What categories of information should *never* be stored (sensitive, embarrassing, transient noise)
- Retention policy: who controls forgetting? User-only, or can Jarvis self-prune?
- Stale memory handling: does it surface uncertainty ("I think I remember...") or state confidently?
- Privacy boundaries: what stays local, what can be sent to APIs?

### Action & Trust Model
- Confirmation gates: which actions require explicit approval? (send message = yes, read calendar = no)
- Blast radius awareness: does it warn before irreversible actions?
- Failure behavior: silent retry, inform + ask, or stop and wait?

### Scope Boundaries
- What Jarvis explicitly *won't* do (scope creep prevention)
- Domains it defers on (medical, financial, legal advice)
- When it escalates vs. handles autonomously

**Deliverable:** A `BEHAVIORAL_SPEC.md` file — the source of truth that the system prompt and memory policies are derived from. Not code, but treated as a first-class artifact.

**Done when:** You can answer "what would Jarvis do if X?" for 10 edge cases without hesitation.

---

## M1 — Bare Agent Loop
**Goal:** "Hello Jarvis" works. Nothing more.

- Python project scaffold (`jarvis/` structure)
- Claude Code CLI integration with tool use
- Basic CLI: type a message, get a response
- 2-3 hardcoded tools (e.g., get current time, open a URL)
- System prompt derived directly from `BEHAVIORAL_SPEC.md`
- No memory — stateless

**Done when:** You can have a multi-turn conversation with tool calls working end-to-end, and the agent's behavior matches the spec.

---

## M2 — Procedural + Hot Semantic Memory
**Goal:** Jarvis feels personalized from turn one, without any retrieval complexity.

- `procedural.md` — standing instructions, always loaded (your preferences, how you like responses, recurring context)
- `hot.json` — always-injected facts: your name, timezone, current projects, key people
- Manual writes only (you edit these files directly)
- Token budget enforced: procedural + hot < 800 tokens total

**Done when:** Jarvis greets you correctly, knows your preferences, and doesn't ask who you are.

**Why M1 before episodic:** Highest ROI per line of code. Static files, no retrieval, immediate payoff.

---

## M3 — Semantic Memory (Entity Store)
**Goal:** Jarvis knows facts about people, projects, and preferences — and keeps them current.

- `/semantic/people/`, `/semantic/projects/`, `/semantic/preferences.json`
- Entity schema: `{ facts: { key: { value, confidence, updated, source } } }`
- Entity detection in query → load relevant entity files into context
- Conflict resolution: low-confidence facts overwrite silently, high-confidence facts flag for confirmation
- Write path: manual + simple CLI command to add/update facts (`jarvis remember "Priya prefers async comms"`)

**Done when:** You can ask "what do I know about Priya?" and get accurate, structured facts. New facts can be added and old ones updated without duplication.

---

## M4 — Episodic Memory
**Goal:** Jarvis remembers what happened in past conversations and retrieves relevant history.

- SQLite + sqlite-vec for local vector storage
- Episode schema: `{ id, timestamp, summary, embedding, entities[], importance, access_count }`
- Write path: after each conversation, auto-generate a 2-3 sentence summary + embedding
- Read path: embed current query → cosine similarity search → inject top-k summaries (not full text)
- Importance scoring at write time: decisions/commitments = high, small talk = low
- Recency boost in retrieval ranking

**Done when:** You can say "what did we decide about the auth refactor last week?" and Jarvis retrieves the right episode.

---

## M5 — Memory Router
**Goal:** Automatic, intelligent context composition — right memory, right amount, every query.

- Query classifier (Haiku-powered, fast + cheap) → tags query with needed memory types
- Token budget manager: allocates slots per memory type
  - System/procedural: 800 tokens
  - Hot semantic: 300 tokens  
  - Retrieved episodic summaries: 600 tokens
  - Entity facts: 300 tokens
  - Working memory (conversation): remainder
- Entity mention detection → auto-load relevant semantic files
- Temporal reference detection → load prospective memories
- "Remember when" → trigger episodic search

**Done when:** You never think about what memory is loaded — Jarvis always has what it needs without you managing it.

---

## M6 — Automated Write Path
**Goal:** Memory writes itself. No manual upkeep required.

Background job runs after every conversation:
- Entity extraction → upsert semantic memory
- Preference detection → update `preferences.json`
- Commitment/decision detection → add to prospective memory (M6)
- Significance scoring → decide whether to write an episode
- `hot.json` refresh based on access frequency patterns

- All writes are async (never block the response)
- Write log for auditability: what was saved and why

**Done when:** You have a week of conversations and your memory stores are meaningfully populated without a single manual edit.

---

## M7 — Prospective Memory
**Goal:** Jarvis tracks future intentions and surfaces them at the right time.

- SQLite table: `{ id, content, due_date, trigger_condition, status, source_episode }`
- Two trigger types:
  - **Time-based**: "remind me Thursday" → fires at session start when due
  - **Condition-based**: "follow up with Priya after the release" → fires when Priya or release is mentioned
- Session start: surface any due prospective memories as a briefing
- Integration hook: optionally sync to calendar/reminders

**Done when:** You say "remind me to follow up on X next week" and Jarvis surfaces it without being asked.

---

## M8 — Summarization & Decay Pipeline
**Goal:** Episodic memory stays useful at scale. Old noise doesn't crowd out new signal.

Nightly job:
- Cluster today's episodes by entity overlap + semantic similarity
- Generate compressed cluster summary
- Archive raw episodes (deprioritized in retrieval)

Weekly job:
- Cluster daily summaries → weekly themes
- Promote durable facts to semantic memory
- Expire completed prospective memories

Monthly job:
- "What's still true?" pass over episodic → elevate to semantic
- Full archive for episodes older than 60 days

**Done when:** After 3 months of use, retrieval quality hasn't degraded and token usage per query hasn't grown.

---

## M9 — Tool Integrations
**Goal:** Jarvis can act on your world, not just talk about it.

- Calendar: read events, create events, find free slots
- Email: search threads, draft replies, send
- Slack: read channels, send messages
- Web search: current information lookup
- File system: read/write local files

Each tool wrapped with memory hooks: significant tool outputs auto-written to episodic memory.

**Done when:** "Schedule a 30-min call with Priya next week and send her a Slack" works end-to-end.

---

## M10 — Voice Layer
**Goal:** The Jarvis *feel*. Talk to it, hear it respond.

- STT: OpenAI Whisper (local) or Deepgram (API) 
- TTS: ElevenLabs for realism, or `pyttsx3` for offline
- Push-to-talk mode first (hold key → record → release → process)
- Voice activity detection for hands-free later

**Done when:** Full conversation without touching the keyboard.

---

## M11 — Always-On & Proactive
**Goal:** Jarvis initiates, not just responds.

- Wake word detection: Picovoice Porcupine ("Hey Jarvis")
- Background process: runs silently, listens for wake word
- Proactive triggers:
  - Meeting starting in 10 min → "You have a call with Priya at 3pm"
  - Overdue prospective memory → surface it
  - Unread urgent Slack → optional nudge
- Menubar presence (macOS): status icon, mute toggle

**Done when:** Jarvis tells you something before you ask.

---

## Milestone Summary

| # | Milestone | What it unlocks |
|---|-----------|-----------------|
| M0 | Behavioral spec | Defines what Jarvis *is* |
| M1 | Bare agent loop | Proof of concept |
| M2 | Procedural + hot semantic | Feels personalized |
| M3 | Semantic entity store | Knows your world |
| M4 | Episodic memory | Remembers the past |
| M5 | Memory router | Smart context, no manual management |
| M6 | Automated write path | Memory maintains itself |
| M7 | Prospective memory | Tracks future intentions |
| M8 | Decay pipeline | Scales without degrading |
| M9 | Tool integrations | Acts on your world |
| M10 | Voice layer | The Jarvis feel |
| M11 | Always-on + proactive | Truly ambient assistant |

---

## What to Build First

Start at M0 — the behavioral spec. Every downstream decision (system prompt, memory policy, confirmation gates) should be traceable back to it. Resist skipping to voice (M10) — the memory architecture (M2–M6) is what separates this from a glorified chatbot.
