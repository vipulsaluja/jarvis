# M0 — Behavioral Spec: Task Breakdown

## Progress
- [ ] = pending  [~] = in progress  [x] = done

## Tasks

- [x] T1: Create `docs/BEHAVIORAL_SPEC.md` with skeleton sections
  File exists with headings for Persona, Interaction Model, Memory Behavior, Action & Trust Model, and Scope Boundaries — content placeholder or empty, structure committed.

- [x] T2: Write the Persona section
  Decisions recorded: tone/address style (formal vs. informal, name use, humor threshold), default response length (terse vs. thorough, when to elaborate), and what makes this Jarvis distinctly personal vs. generic.

- [x] T3: Write the Interaction Model section
  Decisions recorded: clarification policy (ask-before vs. attempt-then-report), confidence threshold for "I'm not sure" responses, proactivity threshold (what warrants an unsolicited message), and interruption policy for when always-on mode exists.

- [x] T4: Write the Memory Behavior section
  Decisions recorded: categories of information never stored, retention policy and who controls forgetting, how stale/uncertain memories are surfaced, and what stays local vs. can be sent to external APIs.

- [x] T5: Write the Action & Trust Model section
  Decisions recorded: which action categories require explicit confirmation (mapped to specific tool types), blast radius warning policy, and failure behavior (silent retry vs. inform+ask vs. stop).

- [x] T6: Write the Scope Boundaries section
  Decisions recorded: explicit list of things Jarvis won't do, domains it defers on (medical, financial, legal), and the line between autonomous handling vs. escalation to the user.

- [x] T7: Validate with 10 edge cases
  Write 10 "what would Jarvis do if X?" scenarios at the bottom of the spec and answer each one using the spec as written — no hesitation or ambiguity in the answers signals the spec is complete.
