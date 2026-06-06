import asyncio
from typing import AsyncIterator, Optional
from llm2sh.config import get_settings

class ShellExecutor:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.process: Optional[asyncio.subprocess.Process] = None

    async def execute(self, command: str) -> AsyncIterator[str]:
        """
        Execute command asynchronously in the configured shell and stream output chunks.
        Supports dry run option.
        """
        if self.settings.dry_run:
            yield f"[Dry Run] Would execute: {command}\n"
            return

        # Resolve shell runner
        shell_path = "/bin/bash"
        if "zsh" in self.settings.shell:
            shell_path = "/bin/zsh"
        elif "fish" in self.settings.shell:
            shell_path = "/usr/bin/fish"

        try:
            self.process = await asyncio.create_subprocess_shell(
                command,
                executable=shell_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
        except Exception as e:
            yield f"Failed to start command: {e}\n"
            return

        if self.process and self.process.stdout:
            while True:
                line_bytes = await self.process.stdout.readline()
                if not line_bytes:
                    break
                yield line_bytes.decode("utf-8", errors="ignore")
                
            await self.process.wait()
            yield f"\n[Process completed with exit code {self.process.returncode}]\n"
            
        self.process = None

    def kill(self) -> bool:
        """Kills the active subprocess if running."""
        if self.process and self.process.returncode is None:
            try:
                self.process.terminate()
                return True
            except Exception:
                try:
                    self.process.kill()
                    return True
                except Exception:
                    pass
        return False
