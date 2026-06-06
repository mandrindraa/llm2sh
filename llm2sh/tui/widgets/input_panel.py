from textual.message import Message
from textual.widgets import Input, Label
from textual.containers import Container

class InputPanel(Container):
    class Submitted(Message):
        def __init__(self, query: str) -> None:
            super().__init__()
            self.query = query

    def compose(self):
        yield Input(placeholder="Describe what you want to do... (Ctrl+Enter to submit)", id="query-input")

    def focus(self) -> None:
        self.query_one("#query-input", Input).focus()

    def set_value(self, val: str) -> None:
        inp = self.query_one("#query-input", Input)
        inp.value = val
        inp.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Fires when the user presses Enter in the Input field."""
        if event.value.strip():
            self.post_message(self.Submitted(event.value))
