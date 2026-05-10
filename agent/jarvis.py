import subprocess
import uuid

from agent.system_prompt import SYSTEM_PROMPT


def chat(message: str, session_id: str, is_first: bool) -> str:
    if is_first:
        cmd = [
            "claude", "-p",
            "--session-id", session_id,
            "--system-prompt", SYSTEM_PROMPT,
            "--permission-mode", "bypassPermissions",
            message,
        ]
    else:
        cmd = [
            "claude", "-p",
            "--resume", session_id,
            "--permission-mode", "bypassPermissions",
            message,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return f"[Error: {result.stderr.strip()}]"
    return result.stdout.strip()


def main():
    session_id = str(uuid.uuid4())
    is_first = True
    print("Jarvis  (type 'quit' or 'exit' to stop)\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            break

        reply = chat(user_input, session_id, is_first)
        is_first = False
        print(f"\nJarvis: {reply}\n")


if __name__ == "__main__":
    main()
