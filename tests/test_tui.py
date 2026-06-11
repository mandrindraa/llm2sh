import pytest
from unittest import mock
import os
from llm2sh.tui.app import LLM2ShApp
from llm2sh.tui.widgets.input_panel import InputPanel
from llm2sh.tui.widgets.history_panel import HistoryPanel
from llm2sh.tui.widgets.result_panel import ResultPanel
from llm2sh.tui.screens.settings import SettingsScreen
from llm2sh.tui.screens.onboarding import OnboardingScreen
from llm2sh.tui.widgets.save_modal import SaveModal
from textual.widgets import Tabs

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

@pytest.mark.asyncio
@mock.patch("llm2sh.core.client.AsyncOpenAI")
async def test_tui_history_selection(mock_openai_class):
    # Mock the client's streaming call
    mock_client = mock.MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Mock chat.completions.create for streaming
    async def mock_create(*args, **kwargs):
        class AsyncGen:
            def __init__(self):
                self.chunks = [
                    mock.MagicMock(choices=[mock.MagicMock(delta=mock.MagicMock(content='{"command": "ls -la", "explanation": "list files", "flag_explanations": {}, "risk_level": "safe", "risk_reason": null, "is_pipeline": false, "estimated_effect": "list files"}'))])
                ]
                self.idx = 0
            def __aiter__(self):
                return self
            async def __anext__(self):
                if self.idx < len(self.chunks):
                    res = self.chunks[self.idx]
                    self.idx += 1
                    return res
                raise StopAsyncIteration
        return AsyncGen()
        
    mock_client.chat.completions.create = mock_create

    # Setup dummy API key
    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-dummy12345"}):
        app = LLM2ShApp()
        async with app.run_test() as pilot:
            history_panel = app.query_one(HistoryPanel)
            history_panel.update_history(["list files", "show status"])
            await pilot.pause()
            
            # Find history list and assert it has children
            list_view = history_panel.query_one("#history-list")
            assert len(list_view.children) == 2
            
            # Select the first item in ListView by clicking it
            await pilot.click(list_view.children[0])
            await pilot.pause()
            
            # Check the input has the correct value
            input_widget = app.query_one("#query-input")
            assert input_widget.value == "list files"
            
            # Check result panel was updated
            result_panel = app.query_one(ResultPanel)
            assert result_panel.current_result is not None
            assert result_panel.current_result.command == "ls -la"


@pytest.mark.asyncio
@mock.patch("llm2sh.core.client.AsyncOpenAI")
async def test_tui_mode_switching(mock_openai):
    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-dummy12345"}):
        app = LLM2ShApp()
        async with app.run_test() as pilot:
            tabs = app.query_one("#mode-tabs", Tabs)
            input_widget = app.query_one("#query-input")
            
            # Switch to Explain mode
            tabs.active = "tab-explain"
            await pilot.pause()
            assert app.current_mode == "explain"
            assert "Paste a command to explain" in input_widget.placeholder

            # Switch to Script mode
            tabs.active = "tab-script"
            await pilot.pause()
            assert app.current_mode == "script"
            assert "Describe the steps for your script" in input_widget.placeholder

            # Toggle mode action (ctrl+x)
            app.action_toggle_mode()
            await pilot.pause()
            assert app.current_mode == "translate"


@pytest.mark.asyncio
@mock.patch("llm2sh.core.client.AsyncOpenAI")
async def test_tui_settings(mock_openai):
    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-dummy12345"}):
        app = LLM2ShApp()
        async with app.run_test() as pilot:
            # Open settings screen via action
            app.action_open_settings()
            await pilot.pause()
            assert isinstance(app.screen, SettingsScreen)
            
            # Click Cancel
            await pilot.click("#settings-cancel-btn")
            await pilot.pause()
            assert not isinstance(app.screen, SettingsScreen)


@pytest.mark.asyncio
@mock.patch("llm2sh.core.client.AsyncOpenAI")
async def test_tui_onboarding(mock_openai):
    # Reset settings singleton to force onboarding
    import llm2sh.config
    llm2sh.config.settings = None
    
    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True):
        app = LLM2ShApp()
        async with app.run_test() as pilot:
            # Onboarding screen should be pushed
            await pilot.pause()
            assert isinstance(app.screen, OnboardingScreen)
            
            # Entering key and saving
            app.screen.query_one("#api-key-input").value = "sk-newkey123"
            await pilot.click("#save-btn")
            await pilot.pause()
            
            # Should dismiss and return to main screen
            assert not isinstance(app.screen, OnboardingScreen)
            assert app.settings.openai_api_key == "sk-newkey123"


@pytest.mark.asyncio
@mock.patch("llm2sh.core.client.AsyncOpenAI")
async def test_tui_save_modal(mock_openai):
    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-dummy12345"}):
        app = LLM2ShApp()
        async with app.run_test() as pilot:
            save_modal = SaveModal(default_filename="test.sh")
            
            # Push save modal
            app.push_screen(save_modal)
            await pilot.pause()
            assert isinstance(app.screen, SaveModal)
            
            # Dismiss with path
            await pilot.click("#save-cancel-btn")
            await pilot.pause()
            assert not isinstance(app.screen, SaveModal)


@pytest.mark.asyncio
@mock.patch("llm2sh.core.client.AsyncOpenAI")
async def test_tui_settings_save(mock_openai):
    # Mock save_settings to prevent writing to real .env
    with mock.patch("llm2sh.tui.screens.settings.save_settings") as mock_save:
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-dummy12345"}):
            app = LLM2ShApp()
            async with app.run_test() as pilot:
                app.action_open_settings()
                await pilot.pause()
                assert isinstance(app.screen, SettingsScreen)
                
                # Update settings fields
                app.screen.query_one("#setting-api-key").value = "sk-newapi123"
                app.screen.query_one("#setting-history-size").value = "15"
                app.screen.query_one("#setting-dry-run").value = True
                
                # Save
                await pilot.click("#settings-save-btn")
                await pilot.pause()
                
                # Check setting singleton updated and save was called
                assert not isinstance(app.screen, SettingsScreen)
                assert app.settings.openai_api_key == "sk-newapi123"
                assert app.settings.history_size == 15
                assert app.settings.dry_run is True
                mock_save.assert_called_once()




