import datetime
import subprocess
import webbrowser

TOOL_DEFINITIONS = [
    {
        "name": "get_current_time",
        "description": "Returns the current local date and time.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "open_url",
        "description": "Opens a URL in the user's default web browser.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to open.",
                }
            },
            "required": ["url"],
        },
    },
    {
        "name": "run_shell_command",
        "description": (
            "Runs a read-only shell command and returns stdout. "
            "Only use for safe, non-destructive commands (ls, cat, pwd, etc.). "
            "Never use for commands that modify system state."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to run.",
                }
            },
            "required": ["command"],
        },
    },
]


def execute_tool(name: str, inputs: dict) -> str:
    if name == "get_current_time":
        now = datetime.datetime.now()
        return now.strftime("%A, %B %-d, %Y at %-I:%M %p")

    if name == "open_url":
        url = inputs["url"]
        webbrowser.open(url)
        return f"Opened {url} in the default browser."

    if name == "run_shell_command":
        command = inputs["command"]
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout.strip()
        if result.returncode != 0:
            return f"Command failed (exit {result.returncode}): {result.stderr.strip()}"
        return output if output else "(no output)"

    return f"Unknown tool: {name}"
