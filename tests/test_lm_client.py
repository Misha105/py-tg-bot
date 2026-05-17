"""Tests for bot.services.lm_client module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from bot.services.lm_client import OpenRouterClient


@pytest.fixture
def client() -> OpenRouterClient:
    return OpenRouterClient(
        api_key="sk-or-test-key",
        base_url="https://openrouter.ai/api/v1",
        default_model="openai/gpt-4o-mini",
        referer="https://github.com/test/bot",
        title="Test Bot",
        timeout=30,
    )


SUCCESS_RESPONSE = {
    "choices": [{"message": {"content": "Hello from OpenRouter"}}],
    "model": "openai/gpt-4o-mini",
    "usage": {"total_tokens": 15},
}


async def test_chat_success(client: OpenRouterClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SUCCESS_RESPONSE

    with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await client.chat(
            messages=[{"role": "user", "content": "Hi"}],
            temperature=0.7,
            max_completion_tokens=1024,
            top_p=0.9,
            presence_penalty=0.3,
            frequency_penalty=0.0,
            verbosity="low",
        )

    assert result == "Hello from OpenRouter"
    mock_post.assert_called_once_with(
        "/chat/completions",
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": "Hi"}],
            "temperature": 0.7,
            "max_completion_tokens": 1024,
            "top_p": 0.9,
            "presence_penalty": 0.3,
            "frequency_penalty": 0.0,
            "verbosity": "low",
        },
    )


async def test_chat_with_system_prompt(client: OpenRouterClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SUCCESS_RESPONSE

    with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        await client.chat(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful",
        )

    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["json"]["messages"][0] == {"role": "system", "content": "You are helpful"}


async def test_chat_model_override(client: OpenRouterClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SUCCESS_RESPONSE

    with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        await client.chat(
            messages=[{"role": "user", "content": "Hi"}],
            model="anthropic/claude-3.5-sonnet",
        )

    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["json"]["model"] == "anthropic/claude-3.5-sonnet"


async def test_chat_headers_included(client: OpenRouterClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SUCCESS_RESPONSE

    with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        await client.chat(messages=[{"role": "user", "content": "Hi"}])

    mock_post.assert_called_once()
    headers = client.client.headers
    assert "Authorization" in headers
    assert headers["Authorization"] == "Bearer sk-or-test-key"
    assert headers["HTTP-Referer"] == "https://github.com/test/bot"
    assert headers["X-Title"] == "Test Bot"


async def test_chat_timeout_raises_timeout_exception(client: OpenRouterClient) -> None:
    with (
        patch.object(client.client, "post", new_callable=AsyncMock) as mock_post,
        patch("bot.services.lm_client.asyncio.sleep", new_callable=AsyncMock),
        pytest.raises(httpx.TimeoutException),
    ):
        mock_post.side_effect = httpx.TimeoutException("Connection timed out")
        await client.chat(messages=[{"role": "user", "content": "Hi"}])


async def test_chat_500_raises_runtime_error(client: OpenRouterClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    http_error = httpx.HTTPStatusError(
        "Server error", request=MagicMock(), response=mock_response
    )

    with (
        patch.object(client.client, "post", new_callable=AsyncMock) as mock_post,
        pytest.raises(RuntimeError, match="OpenRouter error: 500"),
    ):
        mock_post.return_value = mock_response
        mock_response.raise_for_status.side_effect = http_error
        await client.chat(messages=[{"role": "user", "content": "Hi"}])


async def test_chat_invalid_json_raises_value_error(client: OpenRouterClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"bad": "format"}

    with (
        patch.object(client.client, "post", new_callable=AsyncMock) as mock_post,
        pytest.raises(ValueError, match="Invalid LLM response format"),
    ):
        mock_post.return_value = mock_response
        await client.chat(messages=[{"role": "user", "content": "Hi"}])


async def test_chat_null_content_raises_value_error(client: OpenRouterClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": None}}],
        "model": "openai/gpt-4o-mini",
    }

    with (
        patch.object(client.client, "post", new_callable=AsyncMock) as mock_post,
        pytest.raises(ValueError, match="null content"),
    ):
        mock_post.return_value = mock_response
        await client.chat(messages=[{"role": "user", "content": "Hi"}])


async def test_chat_retry_on_429_then_success(client: OpenRouterClient) -> None:
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    mock_response_429.text = "Rate limited"

    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = SUCCESS_RESPONSE

    error_429 = httpx.HTTPStatusError(
        "Rate limited", request=MagicMock(), response=mock_response_429
    )

    with (
        patch.object(client.client, "post", new_callable=AsyncMock) as mock_post,
        patch("bot.services.lm_client.asyncio.sleep", new_callable=AsyncMock),
    ):
        mock_post.side_effect = [error_429, mock_response_200]
        result = await client.chat(messages=[{"role": "user", "content": "Hi"}])

    assert result == "Hello from OpenRouter"
    assert mock_post.call_count == 2


async def test_chat_retry_exhausted_raises_runtime_error(client: OpenRouterClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.text = "Rate limited"

    error_429 = httpx.HTTPStatusError(
        "Rate limited", request=MagicMock(), response=mock_response
    )

    with (
        patch.object(client.client, "post", new_callable=AsyncMock) as mock_post,
        patch("bot.services.lm_client.asyncio.sleep", new_callable=AsyncMock),
        pytest.raises(RuntimeError, match="OpenRouter error: 429"),
    ):
        mock_post.side_effect = [error_429, error_429, error_429]
        await client.chat(messages=[{"role": "user", "content": "Hi"}])

    assert mock_post.call_count == 3


async def test_chat_error_in_200_response_raises_value_error(client: OpenRouterClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"error": {"message": "Model overloaded"}}'
    mock_response.json.return_value = {"error": {"message": "Model overloaded"}}

    with (
        patch.object(client.client, "post", new_callable=AsyncMock) as mock_post,
        pytest.raises(ValueError, match="OpenRouter error: Model overloaded"),
    ):
        mock_post.return_value = mock_response
        await client.chat(messages=[{"role": "user", "content": "Hi"}])
