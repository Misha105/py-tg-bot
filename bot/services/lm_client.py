"""Asynchronous client for OpenRouter API."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 503}


class OpenRouterClient:
    """Async client for interacting with OpenRouter OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        default_model: str,
        referer: str,
        title: str,
        timeout: int,
        max_retries: int = 2,
    ) -> None:
        self.api_key = api_key
        self.default_model = default_model
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=5.0,
                read=timeout,
                write=timeout,
                pool=10.0,
            ),
            limits=httpx.Limits(
                max_connections=50,
                max_keepalive_connections=20,
            ),
            base_url=base_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": referer,
                "X-Title": title,
            },
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()

    async def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        """Send a chat completion request to OpenRouter.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            system_prompt: Optional system prompt to prepend.
            model: Optional model override; defaults to self.default_model.
            temperature: Sampling temperature.

        Returns:
            The assistant's response content string.

        Raises:
            ConnectionError: On network or request failure.
            httpx.TimeoutException: On request timeout (re-raised for handler).
            RuntimeError: On non-2xx HTTP response.
            ValueError: On malformed or unexpected response format.
        """
        payload_messages: list[dict[str, str]] = []
        if system_prompt is not None:
            payload_messages.append({"role": "system", "content": system_prompt})
        payload_messages.extend(messages)

        payload: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": payload_messages,
            "temperature": temperature,
        }

        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.post(
                    "/chat/completions",
                    json=payload,
                )
                if response.status_code in RETRYABLE_STATUS_CODES and attempt < self.max_retries:
                    wait = 2 ** attempt
                    logger.warning(
                        "OpenRouter %s, retry %d/%d in %ds",
                        response.status_code,
                        attempt + 1,
                        self.max_retries,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    continue

                response.raise_for_status()
            except httpx.TimeoutException as exc:
                if attempt < self.max_retries:
                    wait = 2 ** attempt
                    logger.warning(
                        "OpenRouter timeout, retry %d/%d in %ds: %s",
                        attempt + 1,
                        self.max_retries,
                        wait,
                        exc,
                    )
                    await asyncio.sleep(wait)
                    continue
                raise
            except httpx.RequestError as exc:
                if attempt < self.max_retries:
                    wait = 2 ** attempt
                    logger.warning(
                        "OpenRouter request error, retry %d/%d in %ds: %s",
                        attempt + 1,
                        self.max_retries,
                        wait,
                        exc,
                    )
                    await asyncio.sleep(wait)
                    continue
                logger.warning("OpenRouter request failed after retries: %s", exc)
                raise ConnectionError(f"Failed to connect to OpenRouter: {exc}") from exc
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in RETRYABLE_STATUS_CODES and attempt < self.max_retries:
                    wait = 2 ** attempt
                    logger.warning(
                        "OpenRouter %s, retry %d/%d in %ds",
                        exc.response.status_code,
                        attempt + 1,
                        self.max_retries,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    continue
                logger.error(
                    "OpenRouter returned HTTP %s: %s",
                    exc.response.status_code,
                    exc.response.text,
                )
                raise RuntimeError(f"OpenRouter error: {exc.response.status_code}") from exc
            else:
                break

        try:
            data = response.json()
            content: str = data["choices"][0]["message"]["content"]
            if content is None:
                raise ValueError("LLM returned null content")
        except (KeyError, IndexError, json.JSONDecodeError, TypeError) as exc:
            logger.error("Invalid OpenRouter response format: %s", exc)
            raise ValueError("Invalid LLM response format") from exc

        logger.info(
            "OpenRouter response received (model=%s, tokens=%s)",
            data.get("model", "unknown"),
            data.get("usage", {}).get("total_tokens", "N/A"),
        )
        return content
