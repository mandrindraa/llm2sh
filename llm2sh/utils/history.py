import os
import re
from pathlib import Path

def get_recent_history(shell_name: str = "bash", limit: int = 10) -> list[str]:
    """
    Read the last `limit` commands from the history file of the specified shell.
    Gracesfully returns an empty list if files cannot be read or parsed.
    """
    shell_name = shell_name.lower()
    history_file = os.environ.get("HISTFILE")
    
    if not history_file:
        home = Path.home()
        if "zsh" in shell_name:
            history_file = home / ".zsh_history"
        elif "fish" in shell_name:
            history_file = home / ".local/share/fish/fish_history"
        else:
            history_file = home / ".bash_history"
    else:
        history_file = Path(history_file)

    if not os.path.exists(history_file):
        return []

    commands: list[str] = []
    try:
        if "fish" in shell_name:
            # Fish history uses a YAML-like format with '- cmd: ...' lines
            with open(history_file, "r", errors="ignore") as f:
                for line in f:
                    if line.strip().startswith("- cmd:"):
                        cmd = line.split("- cmd:", 1)[1].strip()
                        if cmd:
                            commands.append(cmd)
        elif "zsh" in shell_name:
            # Zsh history line format is: ': 1622549200:0;command' or plain command
            # The colon and semi-colon prefix is optional but common.
            zsh_pattern = re.compile(r"^:\s*\d+:\d+;(.*)$")
            with open(history_file, "rb") as f:
                for line_bytes in f:
                    try:
                        line = line_bytes.decode("utf-8", errors="ignore").strip()
                        if not line:
                            continue
                        match = zsh_pattern.match(line)
                        if match:
                            commands.append(match.group(1))
                        else:
                            commands.append(line)
                    except Exception:
                        continue
        else:
            # Bash history is usually plain text, but lines starting with '#' followed by digits are timestamps.
            with open(history_file, "r", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("#") and line[1:].isdigit():
                        continue
                    commands.append(line)
    except Exception:
        return []

    # Clean and filter commands, keeping the last unique commands up to the limit
    filtered_commands = []
    seen = set()
    for cmd in reversed(commands):
        cmd_clean = cmd.strip()
        if cmd_clean and cmd_clean not in seen:
            filtered_commands.append(cmd_clean)
            seen.add(cmd_clean)
            if len(filtered_commands) >= limit:
                break
                
    return list(reversed(filtered_commands))
