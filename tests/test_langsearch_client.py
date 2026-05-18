"""Tests for bot.services.langsearch_client module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from bot.services.langsearch_client import LangSearchClient


@pytest.fixture
def client() -> LangSearchClient:
    return LangSearchClient(api_key="test-api-key", timeout=10)


async def test_search_success(client: LangSearchClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "code": 200,
        "data": {
            "webPages": {
                "value": [
                    {
                        "name": "Test Title",
                        "url": "https://example.com",
                        "snippet": "Test snippet",
                    }
                ]
            }
        },
    }

    with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await client.search("test query", count=1)

    assert result == "1. Test Title\nURL: https://example.com\nSnippet: Test snippet"
    mock_post.assert_called_once_with(
        "/web-search",
        json={
            "query": "test query",
            "freshness": "noLimit",
            "count": 1,
            "summary": True,
        },
    )


async def test_search_no_api_key() -> None:
    client = LangSearchClient(api_key="")
    result = await client.search("test query")
    assert result is None


async def test_search_empty_results(client: LangSearchClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"code": 200, "data": {"webPages": {"value": []}}}

    with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await client.search("test query")

    assert result == "No search results found."


async def test_search_api_error_code(client: LangSearchClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"code": 500, "msg": "Internal Error"}

    with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await client.search("test query")

    assert result is None


async def test_search_http_error(client: LangSearchClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 500
    error = httpx.HTTPStatusError("Server error", request=MagicMock(), response=mock_response)

    with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = error
        result = await client.search("test query")

    assert result is None


async def test_search_network_error(client: LangSearchClient) -> None:
    with patch.object(client.client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.RequestError("Network error", request=MagicMock())
        result = await client.search("test query")

    assert result is None
