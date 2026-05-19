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


def mask_user_id(user_id: int) -> str:
    """Mask a Telegram user ID for privacy compliance (PII protection)."""
    uid_str = str(user_id)
    if len(uid_str) <= 6:
        return "***"
    return f"{uid_str[:3]}***{uid_str[-3:]}"


def log_access_attempt(user_id: int, chat_type: str, allowed: bool) -> None:
    """Log an access attempt with a masked user ID for privacy.

    Args:
        user_id: Telegram user ID.
        chat_type: Type of the chat (e.g. 'private', 'group').
        allowed: Whether access was granted.
    """
    status = "ALLOWED" if allowed else "BLOCKED"
    masked_uid = mask_user_id(user_id)
    logger.info("Access: %s | Chat: %s | Status: %s", masked_uid, chat_type, status)
