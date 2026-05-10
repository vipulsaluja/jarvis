#!/usr/bin/env python3
"""Stop hook — stamps model info and finalized_at on the session file."""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

SESSION_FILE = os.path.join(os.path.dirname(__file__), "..", "last-session.json")
SESSION_FILE = os.path.abspath(SESSION_FILE)

data = json.load(sys.stdin)
session_id = data.get("session_id", "unknown")

if not os.path.exists(SESSION_FILE):
    # No tool calls yet this session — write a minimal record.
    session = {"session_id": session_id, "tools": {}, "started_at": datetime.now(timezone.utc).isoformat()}
else:
    with open(SESSION_FILE) as f:
        session = json.load(f)
    # Only finalize if same session (don't stomp a newer one).
    if session.get("session_id") != session_id:
        session = {"session_id": session_id, "tools": {}, "started_at": datetime.now(timezone.utc).isoformat()}

try:
    result = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=3)
    version = result.stdout.strip().split()[0] if result.returncode == 0 else "unknown"
except Exception:
    version = "unknown"

session["finalized_at"] = datetime.now(timezone.utc).isoformat()
session["model"] = "claude-sonnet-4-6"
session["claude_code_version"] = version

with open(SESSION_FILE, "w") as f:
    json.dump(session, f, indent=2)
