from textual.screen import ModalScreen
from textual.widgets import Label, Input, Button
from textual.containers import Container, Horizontal

class SaveModal(ModalScreen[str | None]):
    def __init__(self, default_filename: str = "script.sh", **kwargs) -> None:
        super().__init__(**kwargs)
        self.default_filename = default_filename

    def compose(self):
        with Container(id="save-dialog"):
            yield Label("SAVE TO FILE", id="save-dialog-title")
            yield Label("Enter path/filename where you want to save:")
            yield Input(
                value=self.default_filename,
                placeholder="e.g. script.sh, bin/my-tool",
                id="save-path-input"
            )
            with Horizontal(id="save-dialog-buttons"):
                yield Button("Save", variant="primary", id="save-confirm-btn")
                yield Button("Cancel", variant="default", id="save-cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-confirm-btn":
            self.action_submit()
        elif event.button.id == "save-cancel-btn":
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "save-path-input":
            self.action_submit()

    def action_submit(self) -> None:
        path = self.query_one("#save-path-input", Input).value.strip()
        if not path:
            self.notify("Path cannot be empty!", severity="error")
            return
        self.dismiss(path)
