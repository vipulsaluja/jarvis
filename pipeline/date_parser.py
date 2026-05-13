from __future__ import annotations

import re
import subprocess


_PROMPT = """\
Today's date is {today}.

Convert this date/time hint to an ISO-8601 date string (YYYY-MM-DD format).
Hint: "{hint}"

Rules:
- Return ONLY the date string, e.g. 2026-05-15
- If the hint is vague ("soon", "eventually") or cannot be resolved to a specific date, return: none
- Do not include any explanation, punctuation, or extra text"""

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def resolve_due_date(hint: str | None, today: str) -> str | None:
    if not hint or not hint.strip():
        return None

    prompt = _PROMPT.format(today=today, hint=hint.strip())
    result = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True)
    if result.returncode != 0:
        return None

    raw = result.stdout.strip().lower()
    if raw == "none" or not raw:
        return None

    if _DATE_RE.match(raw):
        return raw

    # Claude sometimes wraps in quotes or adds extra text — extract date if present
    match = re.search(r"\d{4}-\d{2}-\d{2}", raw)
    return match.group(0) if match else None
