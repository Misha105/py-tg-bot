"""Message handlers for the Telegram bot."""

import asyncio
import logging
import re
from contextlib import suppress
from datetime import datetime
from typing import Any

import httpx
from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import AppConfig
from bot.services.context_manager import ConversationContext
from bot.services.langsearch_client import LangSearchClient
from bot.services.lm_client import OpenRouterClient

logger = logging.getLogger(__name__)

TELEGRAM_MAX_MESSAGE_LENGTH = 4096

chat_router = Router()


@chat_router.message(Command("start"))
async def handle_start(message: Message) -> None:
    await message.answer("✅ Доступ подтверждён. Бот готов к работе. Отправьте сообщение.")


@chat_router.message(Command("clear"))
async def handle_clear(message: Message, **data: Any) -> None:
    if message.from_user is None:
        return
    context: ConversationContext = data["context"]
    await context.clear(message.from_user.id)
    await message.answer("🗑️ Контекст очищен.")


async def _send_long_message(message: Message, text: str) -> None:
    """Send a long message split into chunks respecting Telegram's limit."""
    chunks = 0
    for i in range(0, len(text), TELEGRAM_MAX_MESSAGE_LENGTH):
        chunk = text[i : i + TELEGRAM_MAX_MESSAGE_LENGTH]
        try:
            await message.answer(text=chunk)
            chunks += 1
        except Exception:
            logger.error("Failed to send message chunk %d", i, exc_info=True)
    logger.info("Sent %d message chunk(s) for response (%s chars)", chunks, len(text))


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
    context: ConversationContext = data["context"]
    langsearch_client: LangSearchClient | None = data.get("langsearch_client")

    if not message.text or not message.text.strip():
        return

    max_len = config.max_input_length
    if len(message.text) > max_len:
        await message.answer(f"⚠️ Сообщение слишком длинное. Максимум: {max_len} символов.")
        return

    if message.from_user is None or message.bot is None:
        return

    user_id = message.from_user.id
    lang_code = message.from_user.language_code or "en"

    bot = message.bot

    await bot.send_chat_action(
        chat_id=message.chat.id,
        action="typing",
    )

    typing_task: asyncio.Task[None] | None = None
    try:
        typing_task = asyncio.create_task(_keep_typing(bot, message.chat.id))
        async with context.acquire(user_id):
            context.history[user_id].append({"role": "user", "content": message.text})
            history = list(context.history[user_id])

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            dynamic_system_prompt = (
                config.system_prompt + f"\n\n[SYSTEM INFO] Current Date and Time: {now_str}"
            )

            search_query = None
            if langsearch_client:
                search_prompt = (
                    f"[SYSTEM INFO] Current Date and Time: {now_str}\n"
                    f"[SYSTEM INFO] User Language Code: {lang_code}\n\n"
                    "Based on the conversation history and the user's latest message, "
                    "generate a concise web search query to find the most relevant and up-to-date information. "
                    "If no search is needed (e.g., casual greeting, generic question, "
                    "or questions about existing context), reply exactly with NO_SEARCH.\n\n"
                    "RULES:\n"
                    "1. Output ONLY the search query or NO_SEARCH.\n"
                    "2. Do NOT add any conversational text (e.g. 'Here is your query:').\n"
                    "3. Do NOT use quotes around the query.\n"
                    "4. Try to form the search query in the appropriate language (based on User Language Code) to get relevant local results.\n\n"
                    "Examples:\n"
                    "User: 'Hi!' -> NO_SEARCH\n"
                    "User: 'What is the current price of Bitcoin?' -> current price of Bitcoin\n"
                    "User: 'Thanks for the info.' -> NO_SEARCH\n"
                    "User: 'Tell me about Apple ESG report 2024.' -> Apple ESG report 2024"
                )
                try:
                    short_history = history[-3:] if len(history) >= 3 else history
                    search_decision = await lm_client.chat(
                        messages=short_history,
                        system_prompt=search_prompt,
                        temperature=0.0,
                        max_completion_tokens=50,
                        thinking_enabled=False,
                    )

                    search_decision = search_decision.strip()
                    search_decision = re.sub(
                        r"^```.*?\n|```$", "", search_decision, flags=re.MULTILINE
                    ).strip()
                    search_decision = search_decision.strip("'\"")

                    if search_decision and "NO_SEARCH" not in search_decision.upper():
                        search_query = search_decision
                except Exception as exc:
                    logger.warning("Failed to generate search query: %s", exc)

            if search_query and langsearch_client:
                logger.info("Performing web search for: %s", search_query)
                try:
                    search_results = await asyncio.wait_for(
                        langsearch_client.search(search_query, count=config.search_result_count),
                        timeout=8.0,
                    )
                except TimeoutError:
                    logger.warning("LangSearch timed out after 8.0s for query: %s", search_query)
                    search_results = None

                if search_results and search_results != "No search results found.":
                    last_msg_content = history[-1]["content"]
                    enhanced_content = (
                        f"--- BACKGROUND WEB CONTEXT (USE IF RELEVANT) ---\n"
                        f"{search_results}\n"
                        f"--- END CONTEXT ---\n\n"
                        f"{last_msg_content}"
                    )
                    history[-1] = {"role": "user", "content": enhanced_content}

            response_text = await lm_client.chat(
                messages=history,
                system_prompt=dynamic_system_prompt,
                temperature=config.temperature,
                max_completion_tokens=config.max_completion_tokens,
                top_p=config.top_p,
                presence_penalty=config.presence_penalty,
                frequency_penalty=config.frequency_penalty,
                verbosity=config.verbosity,
                thinking_enabled=config.thinking_enabled,
                reasoning_effort=config.reasoning_effort,
                seed=config.seed,
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

    await _send_long_message(message, response_text)
    logger.info(
        "User %s received response (%s chars)",
        user_id,
        len(response_text),
    )
