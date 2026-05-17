"""Message handlers for the Telegram bot."""

import logging
from typing import Any

import httpx
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import AppConfig
from bot.services.lm_client import LMStudioClient

logger = logging.getLogger(__name__)

chat_router = Router()


@chat_router.message(Command("start"))
async def handle_start(message: Message) -> None:
    await message.answer("✅ Доступ подтверждён. Бот готов к работе. Отправьте сообщение.")


@chat_router.message()
async def handle_message(
    message: Message,
    **data: Any,
) -> None:
    config: AppConfig = data["config"]
    lm_client: LMStudioClient = data["lm_client"]
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

    if message.bot is None:
        return

    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action="typing",
    )

    try:
        async with context.acquire(user_id):
            context.history[user_id].append({"role": "user", "content": message.text})
            history = list(context.history[user_id])
            response_text = await lm_client.chat(
                messages=history,
                system_prompt=config.system_prompt,
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

    await message.answer(text=response_text[:4096])
    logger.info(
        "User %s received response (%s chars)",
        user_id,
        len(response_text),
    )
