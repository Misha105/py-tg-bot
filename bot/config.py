"""Configuration module for the Telegram bot."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from bot.utils.prompt_loader import load_system_prompt, template_system_prompt


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
    openrouter_default_model: str = "google/gemma-4-31b-it"
    openrouter_referer: str = ""
    openrouter_title: str = "Local Telegram Bot"
    allowed_user_ids: set[int] | None = None
    system_prompt_path: str = "prompts/system.md"
    system_prompt: str = ""
    max_history_messages: int = 10
    max_input_length: int = 4000
    response_timeout: int = 120
    max_completion_tokens: int = 16384
    top_p: float = 0.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    verbosity: str = "max"
    temperature: float = 0.0
    thinking_enabled: bool = True
    reasoning_effort: str = "max"
    seed: int | None = None

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

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, value: float) -> float:
        if not 0.0 <= value <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
        return value

    @field_validator("top_p")
    @classmethod
    def validate_top_p(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("top_p must be between 0.0 and 1.0")
        return value

    @field_validator("presence_penalty", "frequency_penalty")
    @classmethod
    def validate_penalty(cls, value: float) -> float:
        if not -2.0 <= value <= 2.0:
            raise ValueError("penalty must be between -2.0 and 2.0")
        return value

    @field_validator("verbosity")
    @classmethod
    def validate_verbosity(cls, value: str) -> str:
        if value not in ("low", "medium", "high", "xhigh", "max"):
            raise ValueError("verbosity must be one of: low, medium, high, xhigh, max")
        return value

    @field_validator("reasoning_effort")
    @classmethod
    def validate_reasoning_effort(cls, value: str) -> str:
        if value not in ("high", "max"):
            raise ValueError("reasoning_effort must be one of: high, max")
        return value

    @field_validator("seed", mode="before")
    @classmethod
    def parse_seed(cls, value: str | int | None) -> int | None:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return int(value)

    @field_validator("allowed_user_ids", mode="before")
    @classmethod
    def parse_allowed_user_ids(cls, value: str | None) -> set[int] | None:
        if not value or not value.strip():
            return None
        return {int(uid.strip()) for uid in value.split(",") if uid.strip()}

    @model_validator(mode="after")
    def load_system_prompt(self) -> AppConfig:
        raw = load_system_prompt(Path(self.system_prompt_path))
        try:
            self.system_prompt = template_system_prompt(
                raw,
                temperature=self.temperature,
                model=self.openrouter_default_model,
                reasoning_effort=self.reasoning_effort,
                max_completion_tokens=self.max_completion_tokens,
                verbosity=self.verbosity,
                thinking_enabled=self.thinking_enabled,
            )
        except KeyError:
            self.system_prompt = raw
        return self


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Return cached AppConfig instance."""
    return AppConfig()
