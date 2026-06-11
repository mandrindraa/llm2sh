from textual.message import Message
from textual.widgets import ListView, ListItem, Label
from textual.containers import Container

class HistoryPanel(Container):
    class QuerySelected(Message):
        def __init__(self, query: str) -> None:
            super().__init__()
            self.query = query

    def compose(self):
        yield Label("HISTORY", id="history-title")
        yield ListView(id="history-list")

    def update_history(self, queries: list[str]):
        """Clear and rebuild the list of historical queries."""
        list_view = self.query_one("#history-list", ListView)
        list_view.clear()
        # Ensure we add items in reverse order or standard order. Usually standard order so latest is at bottom.
        for q in queries:
            list_view.append(ListItem(Label(f"> {q}")))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle click/selection of a history item and post message to app."""
        if event.item:
            label = event.item.query_one(Label)
            query_text = str(label.content).lstrip("> ")
            self.post_message(self.QuerySelected(query_text))
