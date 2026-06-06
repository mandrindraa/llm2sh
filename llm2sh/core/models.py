from enum import Enum
from pydantic import BaseModel, Field

class RiskLevel(str, Enum):
    SAFE = "safe"
    CAUTION = "caution"
    DANGER = "danger"

class CommandResult(BaseModel):
    command: str = Field(description="The generated shell command")
    explanation: str = Field(description="Plain-English breakdown of what the command does")
    flag_explanations: dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary mapping each flag/option used in the command to its explanation"
    )
    risk_level: RiskLevel = Field(description="The evaluated safety risk level of executing the command")
    risk_reason: str | None = Field(default=None, description="Detailed explanation of the risk, if risk_level is not 'safe'")
    is_pipeline: bool = Field(description="True if the command contains multiple piped commands, False otherwise")
    estimated_effect: str = Field(description="A concise description of the exact effect this command will have on the system")
    clarifying_question: str | None = Field(default=None, description="A clarifying question if the user's request is too ambiguous to generate a command")
