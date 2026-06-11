from textual.screen import Screen
from textual.widgets import Label, Input, Select, Switch, Button
from textual.containers import Container, Horizontal, VerticalScroll
from llm2sh.config import get_settings, save_settings

class SettingsScreen(Screen):
    def compose(self):
        settings = get_settings()
        
        # Available choices for select dropdowns
        model_choices = [
            ("GPT-4o", "gpt-4o"),
            ("GPT-4 Turbo", "gpt-4-turbo"),
            ("GPT-3.5 Turbo", "gpt-3.5-turbo"),
            ("qwen2.5-coder:7b", "qwen2.5-coder:7b"),
        ]
        shell_choices = [
            ("Bash", "bash"),
            ("Zsh", "zsh"),
            ("Fish", "fish"),
        ]
        theme_choices = [
            ("Dark", "dark"),
            ("Light", "light"),
        ]

        with Container(id="settings-dialog"):
            yield Label("SETTINGS", id="settings-title")
            
            with VerticalScroll(id="settings-form"):
                yield Label("OpenAI API Key:")
                yield Input(
                    value=settings.openai_api_key or "",
                    placeholder="sk-...",
                    id="setting-api-key",
                    password=True
                )
                
                yield Label("OpenAI Base URL (Optional):")
                yield Input(
                    value=settings.openai_base_url or "",
                    placeholder="http://...",
                    id="setting-base-url"
                )
                
                yield Label("Model:")
                yield Select(
                    model_choices,
                    value=settings.model or "gpt-4o",
                    id="setting-model"
                )
                
                yield Label("Default Shell:")
                yield Select(
                    shell_choices,
                    value=settings.shell or "bash",
                    id="setting-shell"
                )
                
                yield Label("Theme:")
                yield Select(
                    theme_choices,
                    value=settings.theme or "dark",
                    id="setting-theme"
                )
                
                yield Label("History Context Size:")
                yield Input(
                    value=str(settings.history_size),
                    placeholder="10",
                    id="setting-history-size"
                )
                
                with Horizontal(id="settings-dry-run-row"):
                    yield Label("Dry Run Mode:")
                    yield Switch(
                        value=settings.dry_run,
                        id="setting-dry-run"
                    )
            
            with Horizontal(id="settings-buttons"):
                yield Button("Save", variant="primary", id="settings-save-btn")
                yield Button("Cancel", variant="default", id="settings-cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "settings-save-btn":
            self.action_save()
        elif event.button.id == "settings-cancel-btn":
            self.dismiss(False)

    def action_save(self) -> None:
        settings = get_settings()
        
        # Read API key
        api_key = self.query_one("#setting-api-key", Input).value.strip()
        if not api_key:
            self.notify("API Key cannot be empty!", severity="error")
            return
            
        # Read history size and validate
        history_size_str = self.query_one("#setting-history-size", Input).value.strip()
        try:
            history_size = int(history_size_str)
            if history_size < 0:
                raise ValueError
        except ValueError:
            self.notify("History Context Size must be a positive integer!", severity="error")
            return
            
        # Update settings
        settings.openai_api_key = api_key
        settings.openai_base_url = self.query_one("#setting-base-url", Input).value.strip()
        settings.model = self.query_one("#setting-model", Select).value
        settings.shell = self.query_one("#setting-shell", Select).value
        settings.theme = self.query_one("#setting-theme", Select).value
        settings.history_size = history_size
        settings.dry_run = self.query_one("#setting-dry-run", Switch).value
        
        # Save to .env
        save_settings(settings)
        self.notify("Settings saved successfully!", severity="information")
        self.dismiss(True)
