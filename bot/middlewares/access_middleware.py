"""Access control middleware for the Telegram bot."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message, TelegramObject

from bot.access import is_user_allowed, log_access_attempt


class AccessMiddleware(BaseMiddleware):
    """Middleware that filters access based on user ID and chat type."""

    def __init__(self, allowed_ids: set[int] | None) -> None:
        self.allowed_ids = allowed_ids

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        if event.from_user is None:
            return await handler(event, data)

        user_id = event.from_user.id
        chat_type = event.chat.type

        allowed = is_user_allowed(user_id, self.allowed_ids)
        log_access_attempt(user_id, chat_type, allowed)

        if chat_type != "private":
            return None

        if not allowed:
            return None

        return await handler(event, data)
