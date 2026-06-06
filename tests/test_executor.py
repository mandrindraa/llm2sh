import pytest
import os
import asyncio
from unittest import mock
from llm2sh.core.executor import ShellExecutor
from llm2sh.config import Settings

@pytest.mark.asyncio
async def test_shell_executor_dry_run():
    # Setup settings to dry run
    with mock.patch("llm2sh.core.executor.get_settings") as mock_settings:
        mock_set = mock.MagicMock(spec=Settings)
        mock_set.dry_run = True
        mock_settings.return_value = mock_set
        
        executor = ShellExecutor()
        outputs = []
        async for chunk in executor.execute("echo 'hello'"):
            outputs.append(chunk)
            
        assert len(outputs) == 1
        assert "[Dry Run] Would execute:" in outputs[0]

@pytest.mark.asyncio
async def test_shell_executor_real_execution():
    with mock.patch("llm2sh.core.executor.get_settings") as mock_settings:
        mock_set = mock.MagicMock(spec=Settings)
        mock_set.dry_run = False
        mock_set.shell = "bash"
        mock_settings.return_value = mock_set
        
        executor = ShellExecutor()
        outputs = []
        async for chunk in executor.execute("echo 'hello world test'"):
            outputs.append(chunk)
            
        full_output = "".join(outputs)
        assert "hello world test" in full_output
        assert "completed with exit code 0" in full_output

@pytest.mark.asyncio
async def test_shell_executor_kill():
    with mock.patch("llm2sh.core.executor.get_settings") as mock_settings:
        mock_set = mock.MagicMock(spec=Settings)
        mock_set.dry_run = False
        mock_set.shell = "bash"
        mock_settings.return_value = mock_set
        
        executor = ShellExecutor()
        
        # Start a long-running sleep command
        task = asyncio.create_task(anext(executor.execute("sleep 10")))
        
        # Wait a tiny bit to make sure process starts
        await asyncio.sleep(0.5)
        
        # Kill it
        killed = executor.kill()
        assert killed is True
        
        await task
