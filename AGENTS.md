# Project Guide

## Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.11+ |
| Framework | aiogram 3.28 (async) |
| HTTP | httpx 0.27 (async) |
| Config | pydantic-settings 2.4 + python-dotenv 1.0 |
| Testing | pytest 8.0 + pytest-asyncio 0.24 |
| Lint | ruff 0.8 (E,F,W,I,N,UP,B,SIM,RUF100), ignore E501 |
| Format | black 24.0, line-length 100 |
| Types | mypy 1.13 strict + pydantic.mypy plugin |
| LLM | OpenRouter API (OpenAI-compatible, Bearer auth, HTTP-Referer/X-Title, `provider/model` format) |

## Conventions

- Async-first — no sync I/O in handlers
- Type hints on all functions/methods; `mypy strict`
- Logging via `logging` (`StreamHandler` only) — no `print()`
- PEP8 via `ruff` + `black`
- Docstrings on public classes and functions
- No comments unless requested
- Handler signatures: `**data: Any`, not `data: dict[str, Any]`

## Context7 MCP

Use **Context7 MCP** to fetch current documentation, API references, and code examples for any library or framework (aiogram, httpx, pydantic, pytest, etc.).

Use when you need to:
- Verify API syntax or method signatures
- Find correct usage patterns
- Check behavior in recent versions (e.g., aiogram 3.x vs 2.x)

**Procedure:**
1. `context7_resolve-library-id` — resolve library name to a Context7 ID
2. `context7_query-docs` — retrieve docs and examples

Do NOT use for: refactoring, writing scripts from scratch, debugging business logic, code review, or general programming concepts.

## Output Rules (Caveman Mode)

- **Output only** complete file contents in fenced code blocks. No conversational text, no explanations, no sign-offs.
- **Assume** full project context. Never repeat README, structure, or prior instructions.
- **Token economy:** compress comments, use references (`# See: config.py:20`), skip redundant imports, zero filler.
- **Edit protocol:** output the **entire** file on every change. No partial diffs, no `...` placeholders.
- **Error handling:** if ambiguous or contradictory:
  ```
  !CLARIFY_REQUIRED
  ```
  Stop. Do not guess. Wait for direction.
- **Override Protocol:** structural/architectural changes require `!CONFIRM_CHANGE` and explicit approval.

### Override Examples

Requires `!CONFIRM_CHANGE`:
- New services, middleware, handlers, or deps
- Changing `AppConfig` schema or validation
- Package restructuring or logging architecture changes

Does NOT require override:
- Bug fixes in existing modules
- New tests for existing functionality
- Config value updates
- Minor refactoring preserving interfaces
- Formatting/linting fixes

## Architecture

| File | Purpose |
|---|---|
| `bot/main.py` | Entry point: Bot, Dispatcher, OpenRouterClient, ConversationContext; `AccessMiddleware` on `dp.message`; `dp.workflow_data` with config/lm_client/context; polling with `skip_updates=True` |
| `bot/config.py` | `AppConfig` (pydantic-settings, `env_file=".env"`); strips trailing `/`, validates `https` for OpenRouter, parses `ALLOWED_USER_IDS` to `set[int]`; loads system prompt via `model_validator`; `get_config()` is `@lru_cache(maxsize=1)` |
| `bot/access.py` | `is_user_allowed(user_id, allowed_ids)` — returns `True` if `allowed_ids` is None/empty; `log_access_attempt()` |
| `bot/handlers/chat.py` | `chat_router` — `/start` + catch-all text handler; extracts `config`/`lm_client`/`context` from `**data`; validates input (max 4000 chars); typing action; catches `ConnectionError`, `httpx.TimeoutException`, `ValueError`, generic `Exception`; splits response into 4096-char chunks |
| `bot/middlewares/access_middleware.py` | `AccessMiddleware(BaseMiddleware)` — guards `isinstance(event, Message)` and `from_user is None`; blocks non-private chats and unauthorized users; returns `None` to silently drop |
| `bot/services/lm_client.py` | `OpenRouterClient` — async httpx for `/api/v1/chat/completions`; retry 429/503 with exponential backoff; Bearer auth; raises `ConnectionError`/`RuntimeError`/`ValueError` |
| `bot/services/context_manager.py` | `ConversationContext` — per-user `deque[dict[str, Any]]` with `maxlen`; per-user `asyncio.Lock` via `defaultdict`; `acquire()` context manager, `add_message()`, `get_history()`, `clear()` (atomic pop of history + lock) |
| `bot/utils/prompt_loader.py` | `load_system_prompt(file_path)` — reads markdown, strips; fallback `"You are a helpful, concise assistant..."` |
| `prompts/system.md` | Default system prompt loaded at config init (generic OMEGA PRIME) |
| `prompts/system-deep4pro.md` | Model-specific prompt for DeepSeek V4 Pro (loaded via `.env` override) |
| `scripts/verify_setup.py` | Validates `.env`, OpenRouter connectivity via `/api/v1/models`, project imports |
| `scripts/test_lm_connection.py` | Async httpx test of `/chat/completions` |
| `tests/test_access.py` | Parametrized: `is_user_allowed` (None, empty, allowed, denied) |
| `tests/test_config.py` | `AppConfig` defaults, `ALLOWED_USER_IDS` parsing, trailing slash, invalid URL scheme; `clear_lru_cache` fixture |
| `tests/test_context.py` | ConversationContext: add/get, max_history, clear, empty, isolation; `asyncio_mode = "auto"` |
| `tests/test_lm_client.py` | OpenRouterClient: success, system_prompt, model_override, headers, timeout, 500, invalid JSON, null content, retry 429, retry exhausted |

## Quality Gates

- [ ] **0 hardcoded secrets** — `BOT_TOKEN`, `OPENROUTER_API_KEY` via `.env` only
- [ ] **`.env` mandatory** — `AppConfig` fails without `bot_token` and `openrouter_api_key`
- [ ] **`make test` passes** — 24 tests, `asyncio_mode = "auto"`
- [ ] **`make typecheck` passes** — mypy strict; overrides for `bot.handlers.*` and `bot.middlewares.*` (`warn_return_any = false`)
- [ ] **`make lint` passes** — ruff: E,F,W,I,N,UP,B,SIM,RUF100
- [ ] **`make format` passes** — ruff fix + black
- [ ] **No sync I/O in async handlers**
- [ ] **Inputs validated before LLM calls** — max 4000 chars, empty text check, `from_user is None` guard
- [ ] **Atomic context operations** — `clear()` pops history + lock in same `async with`
- [ ] **Generic errors to user** — handler catches all exceptions, logs details, returns friendly messages
- [ ] **Middleware on `dp.message` only** — guards `isinstance(event, Message)` and `from_user is None`
- [ ] **Prompt from file** — `prompts/system.md` via `prompt_loader.py`; fallback if missing
- [ ] **`get_config()` cached** — `@lru_cache`; tests must call `get_config.cache_clear()` via fixture
- [ ] **Response split into chunks** — `_send_long_message()` sends 4096-char chunks with error logging
- [ ] **No `dp.stop_polling()`** — aiogram 3.x handles shutdown; `finally` closes `lm_client` and `bot.session`
- [ ] **OPENROUTER_API_KEY validated on startup, never logged**
