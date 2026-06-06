import pytest
from unittest import mock
import os
from llm2sh.tui.app import LLM2ShApp
from llm2sh.tui.widgets.input_panel import InputPanel
from llm2sh.tui.widgets.history_panel import HistoryPanel
from llm2sh.tui.widgets.result_panel import ResultPanel

@pytest.mark.asyncio
@mock.patch("llm2sh.core.client.AsyncOpenAI")
async def test_tui_app_mount(mock_openai):
    # Setup dummy API key
    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-dummy12345"}):
        app = LLM2ShApp()
        async with app.run_test() as pilot:
            # Check components are mounted
            assert app.query_one(HistoryPanel) is not None
            assert app.query_one(ResultPanel) is not None
            assert app.query_one(InputPanel) is not None
            
            # Verify input focus
            input_widget = app.query_one("#query-input")
            assert input_widget.has_focus
