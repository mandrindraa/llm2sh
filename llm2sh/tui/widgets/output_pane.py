from textual.containers import ScrollableContainer
from textual.widgets import Label, RichLog

class OutputPane(ScrollableContainer):
    def compose(self):
        yield Label("EXECUTION OUTPUT", id="output-title")
        yield RichLog(id="output-log", highlight=True, markup=True)

    def write_output(self, text: str) -> None:
        """Appends output chunks to the log view."""
        self.query_one("#output-log", RichLog).write(text)

    def clear_output(self) -> None:
        """Clears the log view."""
        self.query_one("#output-log", RichLog).clear()
