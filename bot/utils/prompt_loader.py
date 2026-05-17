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
