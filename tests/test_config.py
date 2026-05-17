"""Tests for bot.config module."""

import pytest

from bot.config import AppConfig


@pytest.fixture(autouse=True)
def clear_lru_cache() -> None:
    from bot.config import get_config

    get_config.cache_clear()


def test_valid_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test_token")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")
    monkeypatch.setenv("OPENROUTER_DEFAULT_MODEL", "openai/gpt-4o-mini")
    config = AppConfig()
    assert config.bot_token == "test_token"
    assert config.openrouter_base_url == "https://openrouter.ai/api/v1"
    assert config.openrouter_default_model == "openai/gpt-4o-mini"
    assert config.max_history_messages == 10
    assert config.response_timeout == 120


def test_allowed_user_ids_parsed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test_token")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")
    monkeypatch.setenv("ALLOWED_USER_IDS", "123, 456")
    config = AppConfig()
    assert config.allowed_user_ids == {123, 456}


def test_allowed_user_ids_int(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test_token")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")
    monkeypatch.delenv("ALLOWED_USER_IDS", raising=False)
    config = AppConfig(allowed_user_ids=42)
    assert config.allowed_user_ids == {42}


def test_allowed_user_ids_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test_token")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")
    monkeypatch.delenv("ALLOWED_USER_IDS", raising=False)
    config = AppConfig(allowed_user_ids=[1, 2, 3])
    assert config.allowed_user_ids == {1, 2, 3}


def test_allowed_user_ids_tuple(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test_token")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")
    monkeypatch.delenv("ALLOWED_USER_IDS", raising=False)
    config = AppConfig(allowed_user_ids=(4, 5))
    assert config.allowed_user_ids == {4, 5}


def test_empty_allowed_user_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test_token")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")
    monkeypatch.setenv("ALLOWED_USER_IDS", "")
    config = AppConfig()
    assert config.allowed_user_ids is None


def test_trailing_slash_removed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test_token")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/")
    config = AppConfig()
    assert config.openrouter_base_url == "https://openrouter.ai/api/v1"


def test_invalid_url_scheme(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test_token")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "http://localhost:1234")
    with pytest.raises(ValueError, match="https scheme"):
        AppConfig()
