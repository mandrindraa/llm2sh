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

def save_settings(settings_instance: Settings) -> None:
    global settings
    settings = settings_instance
    env_path = ".env"
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
    # Map settings fields to env var names
    settings_dict = {
        "OPENAI_BASE_URL": settings_instance.openai_base_url or "",
        "OPENAI_API_KEY": settings_instance.openai_api_key or "",
        "LLM2SH_MODEL": settings_instance.model or "gpt-4o",
        "LLM2SH_SHELL": settings_instance.shell or "bash",
        "LLM2SH_THEME": settings_instance.theme or "dark",
        "LLM2SH_DRY_RUN": str(settings_instance.dry_run).lower(),
        "LLM2SH_HISTORY_SIZE": str(settings_instance.history_size),
    }
    
    updated_keys = set()
    new_lines = []
    for line in lines:
        line_strip = line.strip()
        if not line_strip or line_strip.startswith("#"):
            new_lines.append(line)
            continue
        if "=" in line_strip:
            key, val = line_strip.split("=", 1)
            key = key.strip()
            if key in settings_dict:
                new_lines.append(f"{key}={settings_dict[key]}\n")
                updated_keys.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
            
    # Append any keys that weren't in the original .env
    for key, val in settings_dict.items():
        if key not in updated_keys and val is not None:
            new_lines.append(f"{key}={val}\n")
            
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
