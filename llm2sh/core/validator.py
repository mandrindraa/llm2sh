import re
from llm2sh.core.models import CommandResult, RiskLevel

DANGER_PATTERNS = [
    r"rm\s+-[rf]*[rf]\s+/",          # rm -rf / (or variants like rm -rf /etc, etc.)
    r"dd\s+.*of=/dev/[sh]d",          # dd writing to raw disk
    r"mkfs\.",                        # formatting filesystems
    r"chmod\s+-R\s+777\s+/",          # recursive 777 permissions on root
    r">\s*/dev/[sh]d",                # redirecting directly to raw disks
    r":\s*\(\s*\)\s*\{\s*:\|\s*:\s*&\s*\}\s*;\s*:",     # fork bomb (:(){ :|: & };:)
    r"wget.*\|\s*sh",                 # pipe remote script download directly to shell
    r"curl.*\|\s*(ba)?sh",            # pipe remote script download directly to shell
]

class SafetyValidator:
    def __init__(self) -> None:
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in DANGER_PATTERNS]

    def validate(self, result: CommandResult) -> CommandResult:
        """
        Validate the command against known local danger patterns.
        If a pattern matches, override risk level to DANGER and supply warning explanation.
        """
        command = result.command.strip()
        
        matched_pattern = False
        for pattern in self.compiled_patterns:
            if pattern.search(command):
                matched_pattern = True
                break

        if matched_pattern:
            result.risk_level = RiskLevel.DANGER
            reason = "Matches a local safety rule for highly destructive commands."
            if result.risk_reason:
                result.risk_reason = f"{reason} {result.risk_reason}"
            else:
                result.risk_reason = reason

        return result
