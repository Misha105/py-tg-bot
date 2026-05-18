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
| Web Search | LangSearch API (async httpx) |

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

## Output Rules (Agent Mode)

- **Edit protocol:** Use code editing tools to apply changes directly to the files. Do NOT output the full file contents or large code blocks in the chat.
- **Reporting:** After making changes, provide a short, concise summary of what was changed. No long explanations or conversational filler.
- **Assume** full project context. Never repeat README, structure, or prior instructions.
- **Token economy:** compress comments, use references (`# See: config.py:20`), skip redundant imports, zero filler.
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
| `bot/main.py` | Entry point: Bot, Dispatcher, OpenRouterClient, LangSearchClient, ConversationContext; `AccessMiddleware` on `dp.message`; `dp.workflow_data` injection; polling with `skip_updates=True` |
| `bot/config.py` | `AppConfig` (pydantic-settings, `env_file=".env"`); validates URLs, loads prompts, handles `langsearch_api_key`; `get_config()` is `@lru_cache(maxsize=1)` |
| `bot/access.py` | `is_user_allowed(user_id, allowed_ids)` — returns `True` if `allowed_ids` is None/empty; `log_access_attempt()` |
| `bot/handlers/chat.py` | `chat_router`; validates input; injects dynamic `datetime` and user `language_code`; handles background Web Search with `asyncio.wait_for` timeout and markdown regex cleanup; splits response into 4096-char chunks |
| `bot/middlewares/access_middleware.py` | `AccessMiddleware(BaseMiddleware)` — guards non-private chats and unauthorized users |
| `bot/services/lm_client.py` | `OpenRouterClient` — async httpx for `/api/v1/chat/completions`; retry 429/503 with exponential backoff |
| `bot/services/langsearch_client.py` | `LangSearchClient` — async httpx for `/v1/web-search`; enforces `freshness: noLimit` and returns text snippets |
| `bot/services/context_manager.py` | `ConversationContext` — per-user `deque[dict[str, Any]]`; per-user `asyncio.Lock`; atomic operations |
| `bot/utils/prompt_loader.py` | `load_system_prompt(file_path)` — reads markdown, supports templating variables (e.g. `{temperature}`) |
| `prompts/system.md` | Default system prompt with web search synthesis rules |
| `prompts/system-deep4pro.md` | Model-specific prompt for DeepSeek V4 Pro |
| `scripts/verify_setup.py` | Validates `.env`, OpenRouter connectivity |
| `tests/*` | Pytest suite (40 tests): config, access, context manager, lm_client, and langsearch_client |

## Quality Gates

- [ ] **0 hardcoded secrets** — `BOT_TOKEN`, `OPENROUTER_API_KEY`, `LANGSEARCH_API_KEY` via `.env` only
- [ ] **`.env` mandatory** — `AppConfig` fails without `bot_token` and `openrouter_api_key`
- [ ] **`make test` passes** — 40 tests, `asyncio_mode = "auto"`
- [ ] **`make typecheck` passes** — mypy strict; overrides for `bot.handlers.*` and `bot.middlewares.*`
- [ ] **`make lint` passes** — ruff: E,F,W,I,N,UP,B,SIM,RUF100
- [ ] **`make format` passes** — ruff fix + black
- [ ] **No sync I/O in async handlers**
- [ ] **Inputs validated before LLM calls**
- [ ] **Atomic context operations**
- [ ] **Middleware on `dp.message` only**
- [ ] **Web Search Isolation** — Background queries use sliding history window (last 3 messages) and strict regex parsing
- [ ] **`get_config()` cached** — `@lru_cache`
