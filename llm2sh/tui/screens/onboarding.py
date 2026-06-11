from textual.screen import Screen
from textual.widgets import Label, Input, Button
from textual.containers import Container, Horizontal
from llm2sh.config import get_settings, save_settings

class OnboardingScreen(Screen):
    def compose(self):
        with Container(id="onboarding-dialog"):
            yield Label("WELCOME TO LLM2SH", id="onboarding-title")
            yield Label(
                "Translate plain English descriptions into precise shell commands directly in your terminal.",
                id="onboarding-description"
            )
            yield Label("Enter your OpenAI API Key to get started:", id="onboarding-input-label")
            yield Input(
                placeholder="sk-...",
                id="api-key-input",
                password=True
            )
            with Horizontal(id="onboarding-buttons"):
                yield Button("Save Key & Continue", variant="primary", id="save-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self.action_submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "api-key-input":
            self.action_submit()

    def action_submit(self) -> None:
        api_key_input = self.query_one("#api-key-input", Input)
        api_key = api_key_input.value.strip()
        if not api_key:
            self.notify("API Key cannot be empty!", severity="error")
            return
        
        settings = get_settings()
        settings.openai_api_key = api_key
        save_settings(settings)
        self.notify("API Key saved successfully!", severity="information")
        self.dismiss(True)
