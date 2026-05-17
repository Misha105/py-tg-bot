"""Access control module for the Telegram bot."""

import logging

logger = logging.getLogger("bot.access")


def is_user_allowed(user_id: int, allowed_ids: set[int] | None) -> bool:
    """Check if a user is allowed to interact with the bot.

    Args:
        user_id: Telegram user ID.
        allowed_ids: Set of allowed user IDs, or None for open access.

    Returns:
        True if access is allowed, False otherwise.
    """
    if not allowed_ids:
        return True
    return user_id in allowed_ids


def log_access_attempt(user_id: int, chat_type: str, allowed: bool) -> None:
    """Log an access attempt.

    Args:
        user_id: Telegram user ID.
        chat_type: Type of the chat (e.g. 'private', 'group').
        allowed: Whether access was granted.
    """
    status = "ALLOWED" if allowed else "BLOCKED"
    logger.info("Access: %s | Chat: %s | Status: %s", user_id, chat_type, status)
