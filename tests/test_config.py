"""Tests for bot.config module."""

import pytest

from bot.config import AppConfig


@pytest.fixture(autouse=True)
def clear_lru_cache() -> None:
    from bot.config import get_config

    get_config.cache_clear()


def test_valid_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test_token")
    config = AppConfig()
    assert config.bot_token == "test_token"
    assert config.lm_studio_base_url == "http://localhost:1234/v1"
    assert config.max_history_messages == 10
    assert config.response_timeout == 120


def test_allowed_user_ids_parsed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test_token")
    monkeypatch.setenv("ALLOWED_USER_IDS", "123, 456")
    config = AppConfig()
    assert config.allowed_user_ids == {123, 456}


def test_empty_allowed_user_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test_token")
    monkeypatch.setenv("ALLOWED_USER_IDS", "")
    config = AppConfig()
    assert config.allowed_user_ids is None


def test_trailing_slash_removed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test_token")
    monkeypatch.setenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1/")
    config = AppConfig()
    assert config.lm_studio_base_url == "http://localhost:1234/v1"


def test_invalid_url_scheme(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test_token")
    monkeypatch.setenv("LM_STUDIO_BASE_URL", "ftp://localhost:1234")
    with pytest.raises(ValueError, match="http or https"):
        AppConfig()
