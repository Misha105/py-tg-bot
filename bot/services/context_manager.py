"""Conversation context manager for the Telegram bot."""

from __future__ import annotations

import asyncio
import collections
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any


class ConversationContext:
    """Manages per-user conversation history with async locking."""

    def __init__(self, max_history: int = 10) -> None:
        self.max_history = max_history
        self.history: dict[int, collections.deque[dict[str, Any]]] = collections.defaultdict(
            lambda: collections.deque(maxlen=max_history)
        )
        self.locks: dict[int, asyncio.Lock] = collections.defaultdict(lambda: asyncio.Lock())

    @asynccontextmanager
    async def acquire(self, user_id: int) -> AsyncIterator[None]:
        """Acquire the lock for a specific user.

        Args:
            user_id: Telegram user ID.
        """
        async with self.locks[user_id]:
            yield

    async def add_message(self, user_id: int, role: str, content: str) -> None:
        """Add a message to the user's conversation history.

        Args:
            user_id: Telegram user ID.
            role: Message role (e.g., 'user', 'assistant').
            content: Message content string.
        """
        async with self.locks[user_id]:
            self.history[user_id].append({"role": role, "content": content})

    async def get_history(self, user_id: int) -> list[dict[str, str]]:
        """Retrieve the conversation history for a user.

        Args:
            user_id: Telegram user ID.

        Returns:
            List of message dictionaries, or empty list if none exist.
        """
        async with self.locks[user_id]:
            return list(self.history[user_id])

    async def clear(self, user_id: int) -> None:
        """Clear the conversation history for a specific user.

        Args:
            user_id: Telegram user ID.
        """
        async with self.locks[user_id]:
            self.history.pop(user_id, None)
            self.locks.pop(user_id, None)
