"""Asynchronous client for LM Studio API."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class LMStudioClient:
    """Async client for interacting with LM Studio OpenAI-compatible API."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None,
        default_model: str,
        timeout: int,
    ) -> None:
        self.api_key = api_key
        self.default_model = default_model
        self.client = httpx.AsyncClient(
            timeout=timeout,
            base_url=base_url,
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
        """Send a chat completion request to LM Studio.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            system_prompt: Optional system prompt to prepend.
            model: Optional model override; defaults to self.default_model.
            temperature: Sampling temperature.

        Returns:
            The assistant's response content string.

        Raises:
            ConnectionError: On network or request failure.
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

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = await self.client.post(
                "/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
        except httpx.RequestError as exc:
            logger.warning("LM Studio request failed: %s", exc)
            raise ConnectionError(f"Failed to connect to LM Studio: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            logger.error(
                "LM Studio returned HTTP %s: %s", exc.response.status_code, exc.response.text
            )
            raise RuntimeError(f"LM Studio error: {exc.response.status_code}") from exc

        try:
            data = response.json()
            content: str = data["choices"][0]["message"]["content"]
            if content is None:
                raise ValueError("LLM returned null content")
        except (KeyError, IndexError, json.JSONDecodeError, TypeError) as exc:
            logger.error("Invalid LM Studio response format: %s", exc)
            raise ValueError("Invalid LLM response format") from exc

        logger.info(
            "LM Studio response received (model=%s, tokens=%s)",
            data.get("model", "unknown"),
            data.get("usage", {}).get("total_tokens", "N/A"),
        )
        return content
