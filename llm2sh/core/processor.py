import os
import platform
from typing import Any
from llm2sh.config import get_settings
from llm2sh.utils.history import get_recent_history

class QueryProcessor:
    def __init__(self) -> None:
        self.settings = get_settings()

    def get_os_info(self) -> dict[str, str]:
        """Gathers OS and Linux distribution info if applicable."""
        system = platform.system()
        distro_name = "Unknown"
        distro_version = ""

        if system == "Linux":
            try:
                # platform.freedesktop_os_release is available in Python 3.10+
                info = platform.freedesktop_os_release()
                distro_name = info.get("NAME", "Linux")
                distro_version = info.get("VERSION_ID", "")
            except (AttributeError, OSError):
                # Fallback check
                if os.path.exists("/etc/os-release"):
                    with open("/etc/os-release") as f:
                        for line in f:
                            if line.startswith("NAME="):
                                distro_name = line.strip().split("=")[1].strip('"')
                            elif line.startswith("VERSION_ID="):
                                distro_version = line.strip().split("=")[1].strip('"')
        elif system == "Darwin":
            distro_name = "macOS"
            distro_version = platform.mac_ver()[0]

        return {
            "os": system,
            "distro_name": distro_name,
            "distro_version": distro_version
        }

    def get_shell_version(self, shell: str) -> str:
        """Runs the shell with --version to get version info."""
        try:
            import subprocess
            res = subprocess.run([shell, "--version"], capture_output=True, text=True, timeout=1)
            if res.returncode == 0:
                return res.stdout.strip().split("\n")[0]
        except Exception:
            pass
        return "Unknown version"

    def get_available_tools(self) -> list[str]:
        """Detects which common CLI tools are installed on the system."""
        import shutil
        common_tools = [
            "git", "docker", "kubectl", "jq", "fzf", "tar", "zip", 
            "grep", "sed", "awk", "curl", "wget", "python", "node", 
            "systemctl", "apt", "yum", "brew", "find", "xargs"
        ]
        available = [tool for tool in common_tools if shutil.which(tool) is not None]
        return available

    def build_context(self) -> dict[str, Any]:
        """Builds the context payload to inject into the LLM prompt."""
        os_info = self.get_os_info()
        history = get_recent_history(
            shell_name=self.settings.shell,
            limit=self.settings.history_size
        )
        
        return {
            "os": os_info["os"],
            "distro": f"{os_info['distro_name']} {os_info['distro_version']}".strip(),
            "shell": self.settings.shell,
            "shell_version": self.get_shell_version(self.settings.shell),
            "available_tools": self.get_available_tools(),
            "cwd": os.getcwd(),
            "history": history
        }

    def get_system_prompt(self, mode: str = "translate") -> str:
        """Returns the system instructions for OpenAI Client based on the mode."""
        base_prompt = """You are llm2sh, an expert Unix/Linux shell assistant.
Your job is to convert natural language requests into precise shell commands.

Rules:
1. Always respond with a valid JSON object matching the requested schema. Do not output anything outside the JSON block.
2. Prefer POSIX-compliant commands unless the user's shell is specified in the context.
3. Never guess — if a request is ambiguous or lacks details, include a non-empty string in the `clarifying_question` field.
4. Categorize risk:
   - "safe": Commands that are read-only (like ls, cat, grep) or safely scoped.
   - "caution": Commands that are irreversible but scoped (like modifying files in the local directory, minor deletions).
   - "danger": Commands that are highly destructive, have system-wide scope, or alter system permissions globally (like rm -rf /, dd to raw disk, mkfs, chmod -R 777 /, etc.).
5. If risk_level is "caution" or "danger", you MUST provide a detailed `risk_reason`.
6. Keep explanations concise but complete. Explain each flag used under `flag_explanations`.

Your output JSON must strictly match this schema:
{
  "command": "string",
  "explanation": "string",
  "flag_explanations": {"flag_or_argument": "explanation"},
  "risk_level": "safe" | "caution" | "danger",
  "risk_reason": "string" | null,
  "is_pipeline": boolean,
  "estimated_effect": "string",
  "clarifying_question": "string" | null
}"""

        if mode == "explain":
            return """You are llm2sh, an expert Unix/Linux shell assistant.
The user has provided a shell command. Your job is to explain this command and break it down.

Rules:
1. Always respond with a valid JSON object matching the requested schema. Do not output anything outside the JSON block.
2. In the `command` field, return the exact command passed by the user.
3. Provide a high-level explanation of what the command does in the `explanation` field.
4. Break down each flag and argument used in the command under `flag_explanations`.
5. Categorize risk for the command:
   - "safe": Commands that are read-only or safely scoped.
   - "caution": Commands that are irreversible but scoped.
   - "danger": Commands that are highly destructive, have system-wide scope, etc.
6. If risk_level is "caution" or "danger", you MUST provide a detailed `risk_reason`.

Your output JSON must strictly match this schema:
{
  "command": "string",
  "explanation": "string",
  "flag_explanations": {"flag_or_argument": "explanation"},
  "risk_level": "safe" | "caution" | "danger",
  "risk_reason": "string" | null,
  "is_pipeline": boolean,
  "estimated_effect": "string",
  "clarifying_question": "string" | null
}"""

        elif mode == "script":
            return """You are llm2sh, an expert Unix/Linux shell assistant.
Your job is to write a complete shell/bash script based on the user's multi-step request.

Rules:
1. Always respond with a valid JSON object matching the requested schema. Do not output anything outside the JSON block.
2. In the `command` field, output the entire multi-line bash script, complete with shebang `#!/bin/bash`, proper comments, and robust error handling like `set -euo pipefail`.
3. Provide a high-level explanation of the script's design, overall logic, and execution steps in the `explanation` field.
4. Explain key flags, options, or tools used in the script under `flag_explanations`.
5. Categorize risk for the entire script's execution:
   - "safe": Commands/scripts that are read-only or safely scoped.
   - "caution": Scripts that modify local files or carry moderate risk.
   - "danger": Scripts that execute destructive commands, alter system permissions, or affect system-wide state.
6. If risk_level is "caution" or "danger", you MUST provide a detailed `risk_reason`.

Your output JSON must strictly match this schema:
{
  "command": "string",
  "explanation": "string",
  "flag_explanations": {"flag_or_argument": "explanation"},
  "risk_level": "safe" | "caution" | "danger",
  "risk_reason": "string" | null,
  "is_pipeline": boolean,
  "estimated_effect": "string",
  "clarifying_question": "string" | null
}"""

        return base_prompt

    def build_messages(
        self, 
        query: str, 
        session_history: list[dict[str, str]] | None = None, 
        mode: str = "translate"
    ) -> list[dict[str, str]]:
        """Constructs list of messages for chat completion."""
        messages = [
            {"role": "system", "content": self.get_system_prompt(mode)}
        ]

        # Add context statement
        context = self.build_context()
        context_str = (
            f"User Environment Context:\n"
            f"- OS: {context['os']}\n"
            f"- Distro: {context['distro']}\n"
            f"- Shell: {context['shell']} ({context['shell_version']})\n"
            f"- CWD: {context['cwd']}\n"
            f"- Installed Available Tools: {', '.join(context['available_tools'])}\n"
            f"- Recent Shell History: {context['history']}\n"
        )
        messages.append({"role": "system", "content": context_str})

        # Process session/refinement history if provided
        if session_history:
            messages.extend(session_history)

        # Add current user query / command to explain
        if mode == "explain":
            messages.append({"role": "user", "content": f"Please explain this command: {query}"})
        elif mode == "script":
            messages.append({"role": "user", "content": f"Please generate a script for: {query}"})
        else:
            messages.append({"role": "user", "content": query})
            
        return messages
