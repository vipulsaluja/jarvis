"""
Query classifier — maps a user query to the memory types needed to answer it.

Memory type tags:
  procedural    — always needed; standing instructions and habits. Triggered by every query.
  hot_semantic  — always needed; key facts about the user (name, timezone, projects). Triggered by every query.
  episodic      — needed when the query refers to past conversations or events.
                  Trigger patterns: "remember when", "last time", "did we", "what did we",
                  "previously", "before", "earlier", "last week/month".
  entity        — needed when the query names a specific person, project, or concept that
                  has a semantic entity file. Trigger patterns: named nouns that match files
                  in memory/semantic/people/ or memory/semantic/projects/.
  prospective   — needed when the query involves future intentions, reminders, or time-based
                  references. Trigger patterns: "remind", "don't forget", "tomorrow",
                  "today", "this week", "next week", "upcoming", "schedule".

Return value: a list of one or more tags from the set above. Always includes at least
["procedural", "hot_semantic"].
"""

from __future__ import annotations

import json
import subprocess

VALID_TAGS: list[str] = ["procedural", "hot_semantic", "episodic", "entity", "prospective"]

_SYSTEM_PROMPT = "You are a JSON classifier. Return only a valid JSON array of strings, no explanation, no markdown."

_USER_PROMPT = """\
Which memory types are needed to answer this query?

Choose from: ["procedural", "hot_semantic", "episodic", "entity", "prospective"]

Rules:
- Always include "procedural" and "hot_semantic"
- Add "episodic" if the query mentions past conversations, decisions, or events ("remember when", "last time", "what did we decide", "previously", "did we")
- Add "entity" if the query names a specific person or project ("Priya", "the auth service", "Jarvis project")
- Add "prospective" if the query mentions future plans, reminders, or dates ("remind me", "tomorrow", "this week", "upcoming", "schedule", "don't forget")

Examples:
"What is 2 + 2?" → ["procedural", "hot_semantic"]
"Remember when we discussed PostgreSQL?" → ["procedural", "hot_semantic", "episodic"]
"What do I know about Priya?" → ["procedural", "hot_semantic", "entity"]
"Remind me to follow up next week." → ["procedural", "hot_semantic", "prospective"]
"What did we decide about the Jarvis project last month?" → ["procedural", "hot_semantic", "episodic", "entity"]

Query: """


def classify_query(query: str) -> list[str]:
    """Return the memory type tags needed to answer `query` using a Haiku classifier.

    Falls back to all tags if the classifier call fails or times out.
    """
    prompt = _USER_PROMPT + json.dumps(query)
    try:
        result = subprocess.run(
            [
                "claude", "-p",
                "--model", "claude-haiku-4-5-20251001",
                "--system-prompt", _SYSTEM_PROMPT,
                prompt,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return list(VALID_TAGS)

        raw = result.stdout.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = "\n".join(
                line for line in raw.splitlines()
                if not line.strip().startswith("```")
            ).strip()

        tags = json.loads(raw)
        if not isinstance(tags, list):
            return list(VALID_TAGS)

        # Sanitize: keep only valid tags, always ensure the two base tags
        valid = {t for t in tags if t in VALID_TAGS}
        valid.update({"procedural", "hot_semantic"})
        # Return in canonical order
        return [t for t in VALID_TAGS if t in valid]

    except Exception:
        return list(VALID_TAGS)
