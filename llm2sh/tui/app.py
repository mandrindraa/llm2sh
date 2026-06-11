import json
import pyperclip
from typing import ClassVar
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tabs, Tab, Label, Input
from textual.containers import Container, Horizontal
from textual.binding import Binding
from textual.reactive import reactive

from llm2sh.config import get_settings
from llm2sh.core.client import OpenAIClient
from llm2sh.core.processor import QueryProcessor
from llm2sh.core.validator import SafetyValidator
from llm2sh.core.models import CommandResult, RiskLevel
from llm2sh.core.executor import ShellExecutor

from llm2sh.tui.widgets.history_panel import HistoryPanel
from llm2sh.tui.widgets.input_panel import InputPanel
from llm2sh.tui.widgets.result_panel import ResultPanel
from llm2sh.tui.widgets.output_pane import OutputPane
from llm2sh.tui.widgets.confirm_modal import ConfirmModal
from llm2sh.tui.screens.onboarding import OnboardingScreen
from llm2sh.tui.screens.settings import SettingsScreen
from llm2sh.tui.widgets.save_modal import SaveModal

class LLM2ShApp(App):
    CSS_PATH: ClassVar[str] = "styles/main.tcss"
    
    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+c", "copy_command", "Copy Command", show=True),
        Binding("ctrl+r", "run_command", "Run", show=True),
        Binding("ctrl+k", "kill_process", "Kill", show=True),
        Binding("ctrl+e", "focus_input", "Focus Input", show=True),
        Binding("ctrl+x", "toggle_mode", "Toggle Mode", show=True),
        Binding("ctrl+h", "toggle_history", "History Panel", show=True),
        Binding("ctrl+comma", "open_settings", "Settings", show=True),
        Binding("escape", "clear_input", "Clear / Close Output", show=True),
    ]

    current_mode = reactive("translate")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.settings = get_settings()
        self.processor = QueryProcessor()
        self.client = OpenAIClient()
        self.validator = SafetyValidator()
        self.executor = ShellExecutor()
        self.queries_history: list[str] = []
        self.session_messages: list[dict[str, str]] = []

    def compose(self) -> ComposeResult:
        with Container(id="header"):
            yield Label("llm2sh  v0.1.0", id="title")
            yield Tabs(
                Tab("Translate", id="tab-translate"),
                Tab("Explain", id="tab-explain"),
                Tab("Script", id="tab-script"),
                id="mode-tabs"
            )
        
        with Container(id="main-container"):
            yield HistoryPanel()
            yield ResultPanel()
            
        yield InputPanel()
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(InputPanel).focus()
        
        # Verify API key
        if not self.settings.openai_api_key:
            self.push_screen(OnboardingScreen(), callback=self.on_onboarding_done)

    def on_onboarding_done(self, onboarding_completed: bool) -> None:
        if onboarding_completed:
            from llm2sh.config import get_settings
            self.settings = get_settings()
            self.query_one(InputPanel).focus()

    async def handle_query_submission(self, query: str) -> None:
        """Process natural language query, stream token results, and update display."""
        # Add to history
        if query not in self.queries_history:
            self.queries_history.append(query)
            self.query_one(HistoryPanel).update_history(self.queries_history)

        result_panel = self.query_one(ResultPanel)
        
        # Close output pane if open
        result_panel.show_output(False)
            
        full_query = f"{query}"

        # Build prompt messages
        messages = self.processor.build_messages(full_query, self.session_messages, mode=self.current_mode)
        
        # Accumulate streaming text
        full_response_text = ""
        try:
            async for token in self.client.generate_command_stream(messages):
                full_response_text += token
                result_panel.update_stream(full_response_text)
                
            # Once stream finishes, parse final JSON
            data = json.loads(full_response_text)
            command_result = CommandResult.model_validate(data)
            
            # Local safety checks override
            command_result = self.validator.validate(command_result)
            
            # Store in session message history for refinement loop
            self.session_messages.append({"role": "user", "content": full_query})
            self.session_messages.append({"role": "assistant", "content": full_response_text})
            
            # Handle output
            if command_result.clarifying_question:
                result_panel.display_clarifying_question(command_result.clarifying_question)
            else:
                result_panel.display_result(command_result)
                
        except json.JSONDecodeError:
            # If JSON was malformed, run standard non-stream call as fallback
            try:
                command_result = await self.client.generate_command(messages)
                command_result = self.validator.validate(command_result)
                result_panel.display_result(command_result)
            except Exception as ex:
                result_panel.display_error(str(ex))
        except Exception as e:
            result_panel.display_error(str(e))

    def on_input_panel_submitted(self, message: InputPanel.Submitted) -> None:
        """Handle submissions from the input panel."""
        self.run_worker(self.handle_query_submission(message.query))

    def on_history_panel_query_selected(self, message: HistoryPanel.QuerySelected) -> None:
        """Handle clicks on the history list items."""
        self.query_one(InputPanel).set_value(message.query)
        self.run_worker(self.handle_query_submission(message.query))

    # Execution Engine Integration
    def run_current_command(self, command: str, risk_level: RiskLevel, risk_reason: str | None) -> None:
        """Trigger command execution flow, prompting confirmation if caution/danger."""
        if risk_level == RiskLevel.SAFE:
            self.run_worker(self.execute_command(command))
        else:
            def handle_modal_response(confirmed: bool) -> None:
                if confirmed:
                    self.run_worker(self.execute_command(command))
                else:
                    self.notify("Execution cancelled.")

            self.push_screen(
                ConfirmModal(command, risk_level, risk_reason),
                callback=handle_modal_response
            )

    async def execute_command(self, command: str) -> None:
        """Asynchronously run command and capture output into the OutputPane."""
        res_panel = self.query_one(ResultPanel)
        res_panel.show_output(True)
        
        out_pane = res_panel.query_one(OutputPane)
        out_pane.clear_output()
        out_pane.write_output(f"[bold cyan]$ {command}[/]\n")

        async for chunk in self.executor.execute(command):
            out_pane.write_output(chunk)

    # Keyboard Action Bindings
    def action_copy_command(self) -> None:
        res_panel = self.query_one(ResultPanel)
        if res_panel.current_result:
            pyperclip.copy(res_panel.current_result.command)
            self.notify("Command copied to clipboard!")

    def action_run_command(self) -> None:
        res_panel = self.query_one(ResultPanel)
        if res_panel.current_result:
            self.run_current_command(
                res_panel.current_result.command,
                res_panel.current_result.risk_level,
                res_panel.current_result.risk_reason
            )

    def action_kill_process(self) -> None:
        if self.executor.kill():
            self.notify("Process terminated.")
            res_panel = self.query_one(ResultPanel)
            if res_panel.query_one("#output-pane").styles.display == "block":
                res_panel.query_one(OutputPane).write_output("\n[bold red][Process terminated by user][/]\n")
        else:
            self.notify("No active process to terminate.")

    def action_focus_input(self) -> None:
        self.query_one(InputPanel).focus()

    def action_clear_input(self) -> None:
        res_panel = self.query_one(ResultPanel)
        if res_panel.query_one("#output-pane").styles.display == "block":
            res_panel.show_output(False)
            return
        self.query_one(InputPanel).set_value("")

    # Panel Event Subscriptions
    def on_result_panel_copy_pressed(self, message: ResultPanel.CopyPressed) -> None:
        pyperclip.copy(message.command)
        self.notify("Command copied to clipboard!")

    def on_result_panel_run_pressed(self, message: ResultPanel.RunPressed) -> None:
        self.run_current_command(
            message.command,
            message.risk_level,
            self.query_one(ResultPanel).current_result.risk_reason
        )
        
    def on_result_panel_refine_pressed(self) -> None:
        res_panel = self.query_one(ResultPanel)
        if res_panel.current_result:
            # Refill input with refinement hint
            self.query_one(InputPanel).set_value("but ")
            
    def on_result_panel_save_pressed(self, message: ResultPanel.SavePressed) -> None:
        self.push_screen(
            SaveModal(default_filename="script.sh" if self.current_mode == "script" else "command.sh"),
            callback=lambda path: self.save_to_file(path, message.command)
        )

    def save_to_file(self, path: str | None, content: str) -> None:
        if not path:
            return
        
        async def do_save():
            try:
                import aiofiles
                import os
                dirname = os.path.dirname(path)
                if dirname:
                    os.makedirs(dirname, exist_ok=True)
                async with aiofiles.open(path, "w", encoding="utf-8") as f:
                    await f.write(content)
                if self.current_mode == "script":
                    os.chmod(path, 0o755)
                self.notify(f"Successfully saved to {path}", severity="information")
            except Exception as e:
                self.notify(f"Failed to save: {str(e)}", severity="error")
                
        self.run_worker(do_save())

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        mode_id = event.tab.id
        if mode_id == "tab-translate":
            self.current_mode = "translate"
        elif mode_id == "tab-explain":
            self.current_mode = "explain"
        elif mode_id == "tab-script":
            self.current_mode = "script"

    def watch_current_mode(self, mode: str) -> None:
        input_panel = self.query_one(InputPanel)
        inp = input_panel.query_one("#query-input", Input)
        inp.value = ""
        if mode == "explain":
            inp.placeholder = "Paste a command to explain... (Ctrl+Enter to submit)"
        elif mode == "script":
            inp.placeholder = "Describe the steps for your script... (Ctrl+Enter to submit)"
        else:
            inp.placeholder = "Describe what you want to do... (Ctrl+Enter to submit)"

    def action_toggle_mode(self) -> None:
        tabs = self.query_one("#mode-tabs", Tabs)
        if self.current_mode == "translate":
            tabs.active = "tab-explain"
        elif self.current_mode == "explain":
            tabs.active = "tab-translate"
        elif self.current_mode == "script":
            tabs.active = "tab-translate"

    def action_toggle_history(self) -> None:
        history_panel = self.query_one(HistoryPanel)
        history_panel.display = not history_panel.display

    def action_open_settings(self) -> None:
        self.push_screen(SettingsScreen(), callback=self.on_settings_done)

    def on_settings_done(self, settings_saved: bool) -> None:
        if settings_saved:
            from llm2sh.config import get_settings
            self.settings = get_settings()
            self.query_one(InputPanel).focus()
