import os
from typing import Literal
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_base_url: str = Field(
        default="",
        validation_alias=AliasChoices("OPENAI_BASE_URL", "openai_base_url")
    )

    openai_api_key: str = Field(
        validation_alias=AliasChoices("OPENAI_API_KEY", "openai_api_key")
    )
    model: str = Field(
        default="gpt-4o",
        validation_alias=AliasChoices("LLM2SH_MODEL", "llm2sh_model")
    )
    shell: str = Field(
        default_factory=lambda: os.environ.get("SHELL", "bash").split("/")[-1],
        validation_alias=AliasChoices("LLM2SH_SHELL", "llm2sh_shell")
    )
    theme: Literal["dark", "light"] = Field(
        default="dark",
        validation_alias=AliasChoices("LLM2SH_THEME", "llm2sh_theme")
    )
    dry_run: bool = Field(
        default=False,
        validation_alias=AliasChoices("LLM2SH_DRY_RUN", "llm2sh_dry_run")
    )
    history_size: int = Field(
        default=10,
        validation_alias=AliasChoices("LLM2SH_HISTORY_SIZE", "llm2sh_history_size")
    )

# Singleton instance
settings = None

def get_settings() -> Settings:
    global settings
    if settings is None:
        settings = Settings()
    return settings
