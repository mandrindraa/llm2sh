from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static
from textual.containers import Container
from rich.syntax import Syntax
from llm2sh.core.models import RiskLevel

class ConfirmModal(ModalScreen[bool]):
    def __init__(self, command: str, risk_level: RiskLevel, risk_reason: str | None) -> None:
        super().__init__()
        self.command = command
        self.risk_level = risk_level
        self.risk_reason = risk_reason or "This command may modify or delete files on your system."
        self.countdown = 3 if risk_level == RiskLevel.DANGER else 0
        self.timer = None

    def compose(self):
        theme_class = "caution" if self.risk_level == RiskLevel.CAUTION else "danger"
        title_prefix = "🟡 CAUTION" if self.risk_level == RiskLevel.CAUTION else "🔴 DANGER: High Risk Command!"
        
        with Container(id="dialog", classes=theme_class):
            yield Label(title_prefix, id="dialog-title")
            yield Label(self.risk_reason, id="dialog-message")
            yield Static(Syntax(self.command, "bash", theme="monokai"), id="dialog-command")
            
            with Container(id="dialog-buttons"):
                if self.countdown > 0:
                    yield Button(f"Confirm ({self.countdown})", id="btn-confirm", variant="error", disabled=True)
                else:
                    yield Button("Confirm", id="btn-confirm", variant="success")
                yield Button("Cancel", id="btn-cancel", variant="default")

    def on_mount(self) -> None:
        if self.countdown > 0:
            self.timer = self.set_interval(1.0, self.decrement_countdown)

    def decrement_countdown(self) -> None:
        self.countdown -= 1
        btn = self.query_one("#btn-confirm", Button)
        if self.countdown <= 0:
            btn.label = "Confirm Execution"
            btn.disabled = False
            btn.variant = "success"
            if self.timer:
                self.timer.stop()
        else:
            btn.label = f"Confirm ({self.countdown})"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-confirm":
            self.dismiss(True)
        elif event.button.id == "btn-cancel":
            self.dismiss(False)
