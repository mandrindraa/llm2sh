import os
import pytest
from unittest import mock
from llm2sh.config import Settings, get_settings

def test_default_settings():
    # Mock environment to ensure API key is present but others use defaults
    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-testkey"}):
        settings = Settings(_env_file=None)
        assert settings.openai_api_key == "sk-testkey"
        assert settings.model == "gpt-4o"
        assert settings.theme == "dark"
        assert settings.dry_run is False
        assert settings.history_size == 10

def test_alias_resolution():
    env_vars = {
        "OPENAI_API_KEY": "sk-envkey",
        "LLM2SH_MODEL": "gpt-3.5-turbo",
        "LLM2SH_SHELL": "zsh",
        "LLM2SH_THEME": "light",
        "LLM2SH_DRY_RUN": "true",
        "LLM2SH_HISTORY_SIZE": "25"
    }
    with mock.patch.dict(os.environ, env_vars):
        settings = Settings(_env_file=None)
        assert settings.openai_api_key == "sk-envkey"
        assert settings.model == "gpt-3.5-turbo"
        assert settings.shell == "zsh"
        assert settings.theme == "light"
        assert settings.dry_run is True
        assert settings.history_size == 25

def test_singleton_get_settings():
    import llm2sh.config
    llm2sh.config.settings = None
    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-singleton"}):
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
        assert s1.openai_api_key == "sk-singleton"

