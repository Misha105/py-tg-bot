"""Entry point for the Telegram bot."""

import asyncio
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import get_config
from bot.handlers import chat_router
from bot.middlewares.access_middleware import AccessMiddleware
from bot.services.context_manager import ConversationContext
from bot.services.lm_client import OpenRouterClient

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "bot.log"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

_ON_RAILWAY = bool(os.getenv("RAILWAY_ENVIRONMENT"))

logger = logging.getLogger("bot")


def setup_logging() -> logging.Logger:
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(LOG_FORMAT)

    if not _ON_RAILWAY:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


async def on_startup(bot: Bot) -> None:
    logger.info("Bot started")


async def on_shutdown(bot: Bot) -> None:
    logger.info("Bot stopped")


async def main() -> None:
    setup_logging()
    config = get_config()

    bot = Bot(token=config.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    lm_client = OpenRouterClient(
        api_key=config.openrouter_api_key,
        base_url=config.openrouter_base_url,
        default_model=config.openrouter_default_model,
        referer=config.openrouter_referer,
        title=config.openrouter_title,
        timeout=config.response_timeout,
    )
    logger.info("OpenRouter client initialized at %s", config.openrouter_base_url)

    context = ConversationContext(max_history=config.max_history_messages)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.message.middleware(AccessMiddleware(config.allowed_user_ids))

    dp.workflow_data["config"] = config
    dp.workflow_data["lm_client"] = lm_client
    dp.workflow_data["context"] = context
    dp.include_router(chat_router)

    try:
        await dp.start_polling(bot, skip_updates=True)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Received shutdown signal")
    except asyncio.CancelledError:
        pass
    finally:
        await lm_client.close()
        await bot.session.close()
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
