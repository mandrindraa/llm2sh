import pytest
import os
from unittest import mock
from llm2sh.core.client import OpenAIClient
from llm2sh.core.models import CommandResult, RiskLevel

@pytest.mark.asyncio
@mock.patch("llm2sh.core.client.AsyncOpenAI")
async def test_generate_command(mock_openai_class):
    # Setup mock response for beta.chat.completions.parse
    mock_client = mock.MagicMock()
    mock_openai_class.return_value = mock_client
    
    mock_parsed_result = CommandResult(
        command="ls -la",
        explanation="list files",
        flag_explanations={"-la": "long listing"},
        risk_level=RiskLevel.SAFE,
        risk_reason=None,
        is_pipeline=False,
        estimated_effect="Displays directories",
        clarifying_question=None
    )
    
    mock_response = mock.MagicMock()
    mock_response.choices = [mock.MagicMock(message=mock.MagicMock(parsed=mock_parsed_result))]
    
    # In openai-python, parse is a coroutine
    async def mock_parse(*args, **kwargs):
        return mock_response
        
    mock_client.beta.chat.completions.parse = mock_parse
    
    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
        client = OpenAIClient()
        result = await client.generate_command([{"role": "user", "content": "list files"}])
        
        assert result.command == "ls -la"
        assert result.risk_level == RiskLevel.SAFE
        assert result.explanation == "list files"

@pytest.mark.asyncio
@mock.patch("llm2sh.core.client.AsyncOpenAI")
async def test_generate_command_stream(mock_openai_class):
    mock_client = mock.MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Mock chat.completions.create for streaming
    async def mock_create(*args, **kwargs):
        # Async generator mock
        class AsyncGen:
            def __init__(self):
                self.chunks = [
                    mock.MagicMock(choices=[mock.MagicMock(delta=mock.MagicMock(content="{\"command\""))]),
                    mock.MagicMock(choices=[mock.MagicMock(delta=mock.MagicMock(content=": \"ls\"}"))])
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
    
    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
        client = OpenAIClient()
        stream = client.generate_command_stream([{"role": "user", "content": "list"}])
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
            
        assert "".join(chunks) == "{\"command\": \"ls\"}"
