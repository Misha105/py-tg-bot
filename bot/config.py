"""Configuration module for the Telegram bot."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from bot.utils.prompt_loader import load_system_prompt


class AppConfig(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_default_model: str = "openai/gpt-4o-mini"
    openrouter_referer: str = "https://github.com/your-org/telegram-bot"
    openrouter_title: str = "Local Telegram Bot"
    allowed_user_ids: set[int] | None = None
    system_prompt_path: str = "prompts/system.md"
    system_prompt: str = ""
    max_history_messages: int = 10
    max_input_length: int = 4000
    response_timeout: int = 120

    @field_validator("openrouter_base_url", mode="before")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        url = value.rstrip("/")
        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise ValueError("openrouter_base_url must use https scheme")
        return url

    @field_validator("openrouter_default_model", mode="before")
    @classmethod
    def validate_model(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("openrouter_default_model must not be empty")
        return value.strip()

    @field_validator("allowed_user_ids", mode="before")
    @classmethod
    def parse_allowed_user_ids(cls, value: str | None) -> set[int] | None:
        if not value or not value.strip():
            return None
        return {int(uid.strip()) for uid in value.split(",") if uid.strip()}

    @model_validator(mode="after")
    def load_system_prompt(self) -> AppConfig:
        self.system_prompt = load_system_prompt(Path(self.system_prompt_path))
        return self


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Return cached AppConfig instance."""
    return AppConfig()
