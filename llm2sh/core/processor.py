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
            "cwd": os.getcwd(),
            "history": history
        }

    def get_system_prompt(self) -> str:
        """Returns the system instructions for OpenAI Client."""
        return """You are llm2sh, an expert Unix/Linux shell assistant.
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

    def build_messages(self, query: str, session_history: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
        """Constructs list of messages for chat completion."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ]

        # Add context statement
        context = self.build_context()
        context_str = (
            f"User Environment Context:\n"
            f"- OS: {context['os']}\n"
            f"- Distro: {context['distro']}\n"
            f"- Shell: {context['shell']}\n"
            f"- CWD: {context['cwd']}\n"
            f"- Recent Shell History: {context['history']}\n"
        )
        messages.append({"role": "system", "content": context_str})

        # Process session/refinement history if provided
        if session_history:
            messages.extend(session_history)

        # Add current user query
        messages.append({"role": "user", "content": query})
        return messages
