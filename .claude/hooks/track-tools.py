#!/usr/bin/env python3
"""PostToolUse hook — accumulates per-session tool call counts."""
import json
import os
import sys
from datetime import datetime, timezone

SESSION_FILE = os.path.join(os.path.dirname(__file__), "..", "last-session.json")
SESSION_FILE = os.path.abspath(SESSION_FILE)

data = json.load(sys.stdin)
session_id = data.get("session_id", "unknown")
tool_name = data.get("tool_name", "unknown")

if os.path.exists(SESSION_FILE):
    with open(SESSION_FILE) as f:
        session = json.load(f)
    if session.get("session_id") != session_id:
        session = {"session_id": session_id, "tools": {}, "started_at": datetime.now(timezone.utc).isoformat()}
else:
    session = {"session_id": session_id, "tools": {}, "started_at": datetime.now(timezone.utc).isoformat()}

session["tools"][tool_name] = session["tools"].get(tool_name, 0) + 1
session["last_active"] = datetime.now(timezone.utc).isoformat()

with open(SESSION_FILE, "w") as f:
    json.dump(session, f, indent=2)
