"""Message handlers for the Telegram bot."""

import asyncio
import logging
from contextlib import suppress
from typing import Any

import httpx
from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import AppConfig
from bot.services.lm_client import OpenRouterClient

logger = logging.getLogger(__name__)

chat_router = Router()


@chat_router.message(Command("start"))
async def handle_start(message: Message) -> None:
    await message.answer("✅ Доступ подтверждён. Бот готов к работе. Отправьте сообщение.")


@chat_router.message(Command("clear"))
async def handle_clear(message: Message, **data: Any) -> None:
    if message.from_user is None:
        return
    context: Any = data["context"]
    await context.clear(message.from_user.id)
    await message.answer("🗑️ Контекст очищен.")


async def _keep_typing(bot: Bot, chat_id: int, interval: float = 4.0) -> None:
    while True:
        await asyncio.sleep(interval)
        try:
            await bot.send_chat_action(chat_id=chat_id, action="typing")
        except Exception:
            logger.debug("Failed to send typing action", exc_info=True)


@chat_router.message()
async def handle_message(
    message: Message,
    **data: Any,
) -> None:
    config: AppConfig = data["config"]
    lm_client: OpenRouterClient = data["lm_client"]
    context: Any = data["context"]

    if not message.text or not message.text.strip():
        return

    max_len = config.max_input_length
    if len(message.text) > max_len:
        await message.answer(f"⚠️ Сообщение слишком длинное. Максимум: {max_len} символов.")
        return

    if message.from_user is None:
        return

    user_id = message.from_user.id

    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action="typing",
    )

    typing_task: asyncio.Task[None] | None = None
    try:
        typing_task = asyncio.create_task(
            _keep_typing(message.bot, message.chat.id)
        )
        async with context.acquire(user_id):
            context.history[user_id].append({"role": "user", "content": message.text})
            history = list(context.history[user_id])
            response_text = await lm_client.chat(
                messages=history,
                system_prompt=config.system_prompt,
                temperature=config.temperature,
                max_completion_tokens=config.max_completion_tokens,
                top_p=config.top_p,
                presence_penalty=config.presence_penalty,
                frequency_penalty=config.frequency_penalty,
                verbosity=config.verbosity,
            )
            context.history[user_id].append({"role": "assistant", "content": response_text})
    except ConnectionError as exc:
        logger.error("Handler error: ConnectionError: %s", exc)
        await message.answer("⚠️ Сервис временно недоступен. Попробуйте позже.")
        return
    except httpx.TimeoutException as exc:
        logger.error("Handler error: TimeoutException: %s", exc)
        await message.answer("⏳ Превышено время ожидания. Повторите запрос.")
        return
    except ValueError as exc:
        logger.error("Handler error: ValueError: %s", exc)
        await message.answer("⚠️ Ошибка обработки запроса. Попробуйте переформулировать.")
        return
    except Exception:
        logger.exception("Unhandled handler error")
        await message.answer("⚠️ Временно не могу ответить. Попробуйте позже.")
        return
    finally:
        if typing_task is not None:
            typing_task.cancel()
            with suppress(asyncio.CancelledError):
                await typing_task

    await message.answer(text=response_text[:4096])
    logger.info(
        "User %s received response (%s chars)",
        user_id,
        len(response_text),
    )
