import json
from typing import AsyncIterator
from openai import AsyncOpenAI
from llm2sh.config import get_settings
from llm2sh.core.models import CommandResult

class OpenAIClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)

    async def generate_command(self, messages: list[dict[str, str]]) -> CommandResult:
        """
        Request command translation from OpenAI using beta parser for structured outputs.
        """
        response = await self.client.beta.chat.completions.parse(
            model=self.settings.model,
            messages=messages,
            response_format=CommandResult,
        )
        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise ValueError("Failed to parse response from OpenAI API")
        return parsed

    async def generate_command_stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        """
        Stream the raw JSON token output from OpenAI.
        """
        stream = await self.client.chat.completions.create(
            model=self.settings.model,
            messages=messages,
            response_format={"type": "json_object"},
            stream=True,
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
