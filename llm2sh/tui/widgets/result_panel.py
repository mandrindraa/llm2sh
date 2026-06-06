import re
import pyperclip
from typing import Optional
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from textual.message import Message
from textual.widgets import Static, Button
from textual.containers import Container, ScrollableContainer
from llm2sh.core.models import CommandResult, RiskLevel

class ResultPanel(Container):
    class RunPressed(Message):
        def __init__(self, command: str, risk_level: RiskLevel) -> None:
            super().__init__()
            self.command = command
            self.risk_level = risk_level

    class CopyPressed(Message):
        def __init__(self, command: str) -> None:
            super().__init__()
            self.command = command

    class RefinePressed(Message):
        pass

    class SavePressed(Message):
        def __init__(self, command: str) -> None:
            super().__init__()
            self.command = command

    def compose(self):
        with ScrollableContainer(id="result-scroll"):
            yield Static("Enter a query below to get started.", id="result-status")
            yield Static("", id="command-container")
            yield Static("", id="explanation-container")
            yield Static("", id="flags-container")
            yield Static("", id="risk-container")
        
        with Container(id="action-bar"):
            yield Button("Run", id="btn-run", variant="success", disabled=True)
            yield Button("Copy", id="btn-copy", variant="primary", disabled=True)
            yield Button("Refine", id="btn-refine", variant="default", disabled=True)
            yield Button("Save", id="btn-save", variant="default", disabled=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Propagate button actions to the main application."""
        if not self.current_result:
            return
            
        if event.button.id == "btn-run":
            self.post_message(self.RunPressed(self.current_result.command, self.current_result.risk_level))
        elif event.button.id == "btn-copy":
            self.post_message(self.CopyPressed(self.current_result.command))
        elif event.button.id == "btn-refine":
            self.post_message(self.RefinePressed())
        elif event.button.id == "btn-save":
            self.post_message(self.SavePressed(self.current_result.command))

    def update_stream(self, json_stream_text: str) -> None:
        """Incrementally parse and display the raw JSON stream."""
        self.current_result = None
        self.query_one("#result-status", Static).update("[bold yellow]Generating command...[/]")
        
        # Disable buttons during streaming
        for btn_id in ("btn-run", "btn-copy", "btn-refine", "btn-save"):
            self.query_one(f"#{btn_id}", Button).disabled = True

        parsed = self._parse_partial_json(json_stream_text)
        cmd = parsed.get("command", "")
        exp = parsed.get("explanation", "")

        cmd_container = self.query_one("#command-container", Static)
        if cmd:
            cmd_container.update(Syntax(cmd, "bash", theme="monokai"))
        else:
            cmd_container.update("")

        exp_container = self.query_one("#explanation-container", Static)
        if exp:
            exp_container.update(f"[bold cyan]Explanation:[/]\n{exp}")
        else:
            exp_container.update("")

        # Clear other containers
        self.query_one("#flags-container", Static).update("")
        self.query_one("#risk-container", Static).update("")

    def display_result(self, result: CommandResult) -> None:
        """Display the complete, verified command result and enable actions."""
        self.current_result = result
        self.query_one("#result-status", Static).update("")

        # Display command with syntax highlighting
        cmd_container = self.query_one("#command-container", Static)
        cmd_container.update(Syntax(result.command, "bash", theme="monokai"))

        # Display explanation
        exp_container = self.query_one("#explanation-container", Static)
        exp_container.update(f"[bold cyan]Explanation:[/]\n{result.explanation}")

        # Display flags table if present
        flags_container = self.query_one("#flags-container", Static)
        if result.flag_explanations:
            table = Table(show_header=True, header_style="bold magenta", box=None)
            table.add_column("Flag/Argument", style="cyan")
            table.add_column("Meaning", style="white")
            for flag, explanation in result.flag_explanations.items():
                table.add_row(flag, explanation)
            flags_container.update(table)
        else:
            flags_container.update("")

        # Display risk status
        risk_container = self.query_one("#risk-container", Static)
        risk_text = Text()
        if result.risk_level == RiskLevel.SAFE:
            risk_text.append("Risk Level: ✅ SAFE\n", style="green")
        elif result.risk_level == RiskLevel.CAUTION:
            risk_text.append("Risk Level: ⚠️ CAUTION\n", style="yellow")
        elif result.risk_level == RiskLevel.DANGER:
            risk_text.append("Risk Level: 🛑 DANGER\n", style="bold red")

        if result.risk_reason:
            risk_text.append(f"Reason: {result.risk_reason}\n", style="dim")
        risk_text.append(f"Estimated Effect: {result.estimated_effect}", style="dim")
        risk_container.update(risk_text)

        # Enable buttons
        for btn_id in ("btn-run", "btn-copy", "btn-refine", "btn-save"):
            self.query_one(f"#{btn_id}", Button).disabled = False

    def display_error(self, error_message: str) -> None:
        """Display error text in the panel."""
        self.current_result = None
        self.query_one("#result-status", Static).update(f"[bold red]Error:[/] {error_message}")
        self.query_one("#command-container", Static).update("")
        self.query_one("#explanation-container", Static).update("")
        self.query_one("#flags-container", Static).update("")
        self.query_one("#risk-container", Static).update("")
        
        for btn_id in ("btn-run", "btn-copy", "btn-refine", "btn-save"):
            self.query_one(f"#{btn_id}", Button).disabled = True

    def display_clarifying_question(self, question: str) -> None:
        """Display clarifying question from the model."""
        self.current_result = None
        self.query_one("#result-status", Static).update("")
        self.query_one("#command-container", Static).update(Panel(
            question,
            title="[bold yellow]Clarifying Question[/]",
            border_style="yellow"
        ))
        self.query_one("#explanation-container", Static).update("")
        self.query_one("#flags-container", Static).update("")
        self.query_one("#risk-container", Static).update("")
        
        for btn_id in ("btn-run", "btn-copy", "btn-refine", "btn-save"):
            self.query_one(f"#{btn_id}", Button).disabled = True

    def _parse_partial_json(self, json_str: str) -> dict:
        """Extract partial values from an incomplete JSON stream."""
        result = {}
        # Simple extraction for command value (allowing multiline/escapes)
        cmd_match = re.search(r'"command"\s*:\s*"(.*?)(?:"|$)', json_str, re.DOTALL)
        if cmd_match:
            result["command"] = cmd_match.group(1).replace('\\"', '"').replace('\\n', '\n')
        
        # Simple extraction for explanation value
        exp_match = re.search(r'"explanation"\s*:\s*"(.*?)(?:"|$)', json_str, re.DOTALL)
        if exp_match:
            result["explanation"] = exp_match.group(1).replace('\\"', '"').replace('\\n', '\n')
            
        return result
