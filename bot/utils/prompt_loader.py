"""Utility for loading system prompts from Markdown files."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

FALLBACK_PROMPT = "You are a helpful, concise assistant. Answer accurately and safely."


def load_system_prompt(file_path: str | Path) -> str:
    """Load a system prompt from a Markdown file.

    Args:
        file_path: Path to the prompt file.

    Returns:
        The prompt content as a stripped string, or a fallback default
        if the file cannot be read.
    """
    path = Path(file_path)
    try:
        if not path.exists():
            logger.warning("Prompt file not found: %s", path)
            return FALLBACK_PROMPT
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            logger.warning("Prompt file is empty: %s", path)
            return FALLBACK_PROMPT
        return content
    except (OSError, UnicodeDecodeError) as exc:
        logger.warning("Failed to read prompt file %s: %s", path, exc)
        return FALLBACK_PROMPT


def template_system_prompt(
    prompt: str,
    temperature: float = 0.0,
    model: str = "",
    reasoning_effort: str = "max",
    max_completion_tokens: int = 16384,
    verbosity: str = "max",
) -> str:
    """Replace placeholders in a system prompt with actual config values.

    Args:
        prompt: Raw prompt text with {placeholders}.
        temperature: Sampling temperature value.
        model: Model name/identifier.
        reasoning_effort: Thinking depth setting.
        max_completion_tokens: Max tokens for response.
        verbosity: Response detail level.

    Returns:
        Templated prompt string.
    """
    return prompt.format(
        temperature=temperature,
        model=model,
        reasoning_effort=reasoning_effort,
        max_completion_tokens=max_completion_tokens,
        verbosity=verbosity,
    )
