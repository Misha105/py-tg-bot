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
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-Title"] = title
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
            headers=headers,
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()

    async def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_completion_tokens: int | None = None,
        top_p: float | None = None,
        presence_penalty: float | None = None,
        frequency_penalty: float | None = None,
        verbosity: str | None = None,
        thinking_enabled: bool = True,
        reasoning_effort: str | None = None,
        seed: int | None = None,
    ) -> str:
        """Send a chat completion request to OpenRouter.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            system_prompt: Optional system prompt to prepend.
            model: Optional model override; defaults to self.default_model.
            temperature: Sampling temperature.
            max_completion_tokens: Upper limit for generated tokens.
            top_p: Nucleus sampling threshold.
            presence_penalty: Penalty for token repetition based on presence.
            frequency_penalty: Penalty for token repetition based on frequency.
            verbosity: Response verbosity level (low, medium, high).
            thinking_enabled: Enable chain-of-thought reasoning (DeepSeek V4 Pro).
            reasoning_effort: Thinking depth (high, max).
            seed: Deterministic seed for reproducible responses.

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

        if max_completion_tokens is not None:
            payload["max_completion_tokens"] = max_completion_tokens
        if top_p is not None:
            payload["top_p"] = top_p
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty
        if verbosity is not None:
            payload["verbosity"] = verbosity
        model_name = model or self.default_model
        is_deepseek = "deepseek" in model_name.lower()
        if thinking_enabled and is_deepseek:
            payload["thinking"] = {"type": "enabled"}
            if reasoning_effort is not None:
                payload["reasoning_effort"] = reasoning_effort
        elif thinking_enabled and not is_deepseek:
            logger.debug("thinking_enabled skipped: model %s does not support thinking", model_name)
        if seed is not None:
            payload["seed"] = seed

        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.post(
                    "/chat/completions",
                    json=payload,
                )
                response.raise_for_status()
            except httpx.TimeoutException as exc:
                if attempt < self.max_retries:
                    wait = 2**attempt
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
                    wait = 2**attempt
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
                if (
                    exc.response.status_code in RETRYABLE_STATUS_CODES
                    and attempt < self.max_retries
                ):
                    wait = 2**attempt
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
            if "error" in data:
                error_info = data["error"]
                if isinstance(error_info, dict):
                    error_msg = error_info.get("message", str(error_info))
                else:
                    error_msg = str(error_info)
                logger.error("OpenRouter error in 200 response: %s", error_msg)
                raise ValueError(f"OpenRouter error: {error_msg}")

            choice = data["choices"][0]
            message_data = choice.get("message") or {}
            finish_reason = choice.get("finish_reason", "unknown")

            actual_model = data.get("model", "unknown")
            if actual_model != "unknown" and model_name not in actual_model:
                logger.warning(
                    "Model mismatch: requested %s, got %s",
                    model_name,
                    actual_model,
                )

            reasoning_content: str | None = message_data.get("reasoning_content")
            if reasoning_content is not None:
                logger.info(
                    "reasoning_content received (%d chars) for model %s",
                    len(reasoning_content),
                    actual_model,
                )

            content: str | None = message_data.get("content")
            refusal: str | None = message_data.get("refusal")

            if refusal is not None:
                refusal_str = refusal[:200]
                logger.warning("LLM returned refusal: %s", refusal_str)
                raise ValueError(f"LLM refused to answer: {refusal_str}")

            if content is None:
                logger.error(
                    "LLM returned null content (finish_reason=%s, model=%s, body=%s)",
                    finish_reason,
                    actual_model,
                    response.text[:500],
                )
                raise ValueError("LLM returned null content")

            if finish_reason == "length":
                logger.warning(
                    "LLM response truncated due to max_completion_tokens (model=%s)",
                    actual_model,
                )
        except (KeyError, IndexError, json.JSONDecodeError, TypeError) as exc:
            logger.error(
                "Invalid OpenRouter response format: %s | body: %s",
                exc,
                response.text[:500],
            )
            raise ValueError("Invalid LLM response format") from exc

        logger.info(
            "OpenRouter response received (model=%s, tokens=%s, finish_reason=%s)",
            actual_model,
            data.get("usage", {}).get("total_tokens", "N/A"),
            finish_reason,
        )
        return content
