# PROJECT AGENTS & AI WORKFLOW

## 📦 STACK & CONVENTIONS

| Layer | Technology |
|---|---|
| Runtime | Python 3.11+ |
| Framework | aiogram 3.28 (async Telegram bot) |
| HTTP Client | httpx 0.27 (async) |
| Config | pydantic-settings 2.4 + python-dotenv 1.0 |
| Testing | pytest 8.0 + pytest-asyncio 0.24 |
| Linting | ruff 0.8 (E,F,W,I,N,UP,B,SIM,RUF100), ignore E501 |
| Formatting | black 24.0, line-length 100 |
| Type Checking | mypy 1.13 strict mode + pydantic.mypy plugin |
| LLM Backend | OpenRouter API (OpenAI-compatible, Bearer auth, HTTP-Referer/X-Title headers required, provider/model naming) |

**Conventions:**
- Async-first architecture — no sync I/O in handlers
- Type hints mandatory on all functions and methods; `mypy strict` enforced
- Logging only (`logging` module with `RotatingFileHandler` 5MB/3 backups + `StreamHandler`) — no `print()` in production code
- Strict PEP8, enforced via `ruff` + `black`
- Docstrings on public classes and functions
- No comments unless explicitly requested
- Handler signatures use `**data: Any`, NOT `data: dict[str, Any]`

---

## 🦥 CAVEMAN MODE (ENFORCED)

All AI assistants operating on this repository MUST follow these rules:

### OUTPUT RULE
Return ONLY complete file contents in fenced code blocks. NO conversational text. NO explanations. NO "Sure!", "Here is...", or sign-offs.

### CONTEXT ASSUMPTION
Assume full project context. NEVER repeat README, structure, or prior instructions. Reference files directly (`config.py:20`).

### TOKEN ECONOMY
- Compress comments to minimum
- Use references instead of repetition (`# See: config.py:20`)
- Skip redundant imports if unchanged
- Prefer minimal, production-ready code
- Zero filler, zero padding

### EDIT PROTOCOL
When modifying a file, output the **ENTIRE** file. Do NOT use partial diffs, `...` placeholders, or "rest unchanged" patterns.

### ERROR HANDLING
If a request is ambiguous, contradicts architecture, or requires assumptions that could break the system:
```
!CLARIFY_REQUIRED
```
Stop. Do not guess. Wait for explicit direction.

---

## 🗺️ ARCHITECTURE MAP

| File | Purpose |
|---|---|
| `bot/main.py` | Entry point — creates Bot, Dispatcher, OpenRouterClient, ConversationContext; registers `AccessMiddleware` on `dp.message`; sets `dp.workflow_data` with config/lm_client/context; starts polling with `skip_updates=True` |
| `bot/config.py` | `AppConfig` (pydantic-settings, `env_file=".env"`); `@field_validator` strips trailing `/` from URL, validates `https` scheme for OpenRouter, parses `ALLOWED_USER_IDS` comma-string to `set[int]`; `@model_validator` loads system prompt via `prompt_loader`; `get_config()` is `@lru_cache(maxsize=1)` |
| `bot/access.py` | Pure functions: `is_user_allowed(user_id, allowed_ids)` returns `True` if `allowed_ids` is `None`/empty; `log_access_attempt()` logs `ALLOWED`/`BLOCKED` status |
| `bot/handlers/chat.py` | `chat_router` with `/start` command + catch-all text handler; extracts `config`, `lm_client`, `context` from `**data`; validates input length (`max_input_length=4000`); sends typing action; handles `ConnectionError`, `httpx.TimeoutException`, `ValueError`, generic `Exception`; truncates response to 4096 chars |
| `bot/middlewares/access_middleware.py` | `AccessMiddleware(BaseMiddleware)` — checks `isinstance(event, Message)` and `event.from_user is None` guards; blocks non-private chats and unauthorized users; returns `None` to silently drop, passes to handler otherwise |
| `bot/services/lm_client.py` | `OpenRouterClient` — async httpx client for OpenRouter `/api/v1/chat/completions`; retry logic for 429/503 with exponential backoff; Bearer auth; `HTTP-Referer`/`X-Title` headers; raises `ConnectionError` on `RequestError`, `RuntimeError` on `HTTPStatusError`, `ValueError` on null/malformed content |
| `bot/services/context_manager.py` | `ConversationContext` — per-user `deque[dict[str, Any]]` with `maxlen`; `asyncio.Lock` per user via `defaultdict`; `acquire()` context manager, `add_message()`, `get_history()`, `clear()` (atomic pop of history + lock within same `async with`) |
| `bot/utils/prompt_loader.py` | `load_system_prompt(file_path)` — reads markdown file, returns stripped content; fallback `"You are a helpful, concise assistant..."` on missing/empty/unreadable file |
| `prompts/system.md` | System prompt loaded at config init via `model_validator` |
| `scripts/verify_setup.py` | Validates `.env` (BOT_TOKEN format, OPENROUTER_API_KEY prefix, https scheme), tests OpenRouter connectivity via `/api/v1/models` endpoint, checks project imports |
| `scripts/test_lm_connection.py` | Async httpx test of `/chat/completions` with "Hello" message |
| `tests/test_access.py` | Parametrized tests for `is_user_allowed` (None, empty set, allowed, denied) |
| `tests/test_config.py` | Tests `AppConfig` defaults, `ALLOWED_USER_IDS` parsing, trailing slash removal, invalid URL scheme; `clear_lru_cache` fixture auto-clears `get_config` cache |
| `tests/test_context.py` | Tests `ConversationContext`: add/get, max_history truncation, clear, empty history, user isolation; no `@pytest.mark.asyncio` (auto mode) |
| `tests/test_lm_client.py` | Tests `OpenRouterClient`: success, system_prompt, model_override, headers, timeout, 500 error, invalid JSON, null content, retry 429, retry exhausted |

---

## ✅ QUALITY & SAFETY GATES

- [ ] **0 hardcoded secrets** — `BOT_TOKEN`, `OPENROUTER_API_KEY` via `.env` only
- [ ] **`.env` mandatory** — `AppConfig` requires `bot_token` and `openrouter_api_key`; fails without them
- [ ] **pytest must pass** — `make test` exits 0 (24 tests, `asyncio_mode = "auto"`)
- [ ] **mypy strict clean** — `make typecheck` exits 0; overrides for `bot.handlers.*` and `bot.middlewares.*` (`warn_return_any = false`)
- [ ] **ruff clean** — `make lint` exits 0; rules: E,F,W,I,N,UP,B,SIM,RUF100
- [ ] **black formatted** — `make format` applies ruff fix + black
- [ ] **No sync I/O in async handlers** — all handlers use `async/await`
- [ ] **Validate inputs before LLM calls** — `max_input_length=4000` guard, empty text check, `from_user is None` guard
- [ ] **Atomic context operations** — `clear()` pops history and lock within same `async with` block
- [ ] **Generic errors to user** — handler catches `ConnectionError`, `TimeoutException`, `ValueError`, `Exception` — returns user-friendly messages, logs details
- [ ] **Middleware scope** — `AccessMiddleware` registered on `dp.message`, not `dp.update`; guards `isinstance(event, Message)` and `from_user is None`
- [ ] **Prompt file loading** — system prompt from `prompts/system.md` via `prompt_loader.py`; fallback used if missing/empty/unreadable
- [ ] **`get_config()` is `@lru_cache`** — tests must call `get_config.cache_clear()` via fixture
- [ ] **Response truncation** — `message.answer(text=response_text[:4096])` respects Telegram limit
- [ ] **No `dp.stop_polling()`** — aiogram 3.x handles shutdown; `finally` block closes `lm_client` and `bot.session`
- [ ] **OPENROUTER_API_KEY validated on startup, never logged in plaintext**
- [ ] **Model specified in `provider/model` format** (e.g., `openai/gpt-4o-mini`)

---

## ⚠️ OVERRIDE PROTOCOL

Caveman Mode is the **default** for all operations.

For structural or architectural changes, the AI MUST output:
```
!CONFIRM_CHANGE
```
and wait for explicit user approval before proceeding.

**Examples requiring `!CONFIRM_CHANGE`:**
- Adding new service layers or middleware
- Changing `AppConfig` schema or validation logic
- Modifying handler signatures or dispatcher setup
- Introducing new dependencies
- Restructuring `bot/` package layout
- Changing logging architecture (e.g., adding QueueHandler)

**Examples NOT requiring override:**
- Bug fixes within existing modules
- Adding tests for existing functionality
- Updating configuration values
- Minor refactoring that preserves interfaces
- Formatting/linting fixes
