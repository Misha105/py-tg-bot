# Telegram Bot (OpenRouter + aiogram 3)

## 📦 Overview

Telegram bot that connects to cloud LLMs via OpenRouter's OpenAI-compatible API. Built with **aiogram 3.x**, **pydantic-settings**, and **httpx**.

**Features:**
- User whitelisting via `ALLOWED_USER_IDS`
- Per-user conversation history with configurable retention
- System prompt loaded from `prompts/system.md`
- Graceful error handling with retry logic (429/503)
- Async architecture with `asyncio.Lock` for thread-safe context management
- OpenRouter analytics headers (`HTTP-Referer`, `X-Title`)

**Stack:**
| Component | Technology |
|---|---|
| Framework | aiogram 3.x |
| Config | pydantic-settings + python-dotenv |
| HTTP Client | httpx (async) |
| Testing | pytest + pytest-asyncio |
| LLM Backend | OpenRouter API (OpenAI-compatible) |

---

## 🛠 Prerequisites

| Requirement | Version / Details |
|---|---|
| Python | 3.11+ |
| OpenRouter API Key | Get it at [openrouter.ai/keys](https://openrouter.ai/keys) |
| Telegram Bot Token | Obtained from [@BotFather](https://t.me/BotFather) |

> **Important:** You must have a valid OpenRouter API key before starting the bot. Free models are available — no credit card required.

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd py-tg-bot
```

### 2. Create a virtual environment

```bash
# Linux / macOS
python -m venv .venv
source .venv/bin/activate

# Windows (Command Prompt)
python -m venv .venv
.venv\Scripts\activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get an OpenRouter API key

1. Go to [openrouter.ai/keys](https://openrouter.ai/keys)
2. Create a new key
3. Copy the key (starts with `sk-or-v1-`)

### 5. Configure environment

```bash
# Linux / macOS
cp .env.example .env

# Windows (Command Prompt)
copy .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

Edit `.env` and set at least `BOT_TOKEN` and `OPENROUTER_API_KEY`:

```env
BOT_TOKEN=your_telegram_bot_token_here
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### 6. Run the bot

```bash
python -m bot.main
```

You should see logs indicating the bot has started and is polling for updates. Send `/start` to your bot in Telegram to begin.

---

## ⚙️ Configuration

All settings are managed via environment variables or a `.env` file. The bot uses `pydantic-settings` for validation and `@lru_cache` for config caching.

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `BOT_TOKEN` | `str` | — | **Yes** | Telegram bot token from @BotFather |
| `OPENROUTER_API_KEY` | `str` | — | **Yes** | OpenRouter API key (starts with `sk-or-v1-` or `sk-`) |
| `OPENROUTER_BASE_URL` | `str` | `https://openrouter.ai/api/v1` | No | Base URL of the OpenRouter API (must use https) |
| `OPENROUTER_DEFAULT_MODEL` | `str` | `openai/gpt-4o-mini` | No | Default model in `provider/model` format |
| `OPENROUTER_REFERER` | `str` | `https://github.com/your-org/telegram-bot` | No | HTTP-Referer header for OpenRouter analytics |
| `OPENROUTER_TITLE` | `str` | `Local Telegram Bot` | No | X-Title header for OpenRouter usage tracking |
| `ALLOWED_USER_IDS` | `str` | `""` | No | Comma-separated list of allowed Telegram user IDs. **Empty = open access** |
| `SYSTEM_PROMPT_PATH` | `str` | `prompts/system.md` | No | Path to the system prompt markdown file |
| `MAX_HISTORY_MESSAGES` | `int` | `10` | No | Maximum number of messages retained per conversation |
| `MAX_INPUT_LENGTH` | `int` | `4000` | No | Maximum user message length in characters |
| `RESPONSE_TIMEOUT` | `int` | `120` | No | HTTP read/write timeout in seconds for LLM requests |

> **Note on `SYSTEM_PROMPT`:** The system prompt is **not** stored in `.env`. It is loaded from the file specified in `SYSTEM_PROMPT_PATH` (default: `prompts/system.md`) via `@model_validator(mode="after")`. Edit that file directly to customize the bot's behavior.

> **Note on model names:** OpenRouter uses `provider/model` format (e.g., `openai/gpt-4o-mini`, `anthropic/claude-3.5-sonnet`). See [openrouter.ai/models](https://openrouter.ai/models) for the full list.

---

## 🧪 Testing & Quality

### Run all tests

```bash
python -m pytest tests/ -v --tb=short
```

### Generate coverage report

```bash
# Install coverage dependencies if not already present
pip install pytest-cov

# Run tests with coverage
python -m pytest --cov=bot --cov-report=term-missing
```

### Verify setup (environment + connectivity)

```bash
python -m scripts/verify_setup
```

### Test OpenRouter connection directly

```bash
python -m scripts/test_lm_connection
```

### Test configuration notes

- `pytest-asyncio` is configured with `asyncio_mode = "auto"` — no `@pytest.mark.asyncio` decorator needed
- Tests must **not** depend on OpenRouter or Telegram API
- Use `monkeypatch.setenv()` for config tests, not `.env` file manipulation
- Call `get_config.cache_clear()` before creating `AppConfig` instances in tests

---

## 🔧 Troubleshooting

### 401/403 Unauthorized (Invalid API Key)

| Symptom | Solution |
|---|---|
| Bot fails with `OpenRouter error: 401` or `403` | 1. Verify `OPENROUTER_API_KEY` in `.env` is correct and not expired<br>2. Key must start with `sk-or-v1-` or `sk-`<br>3. Regenerate key at [openrouter.ai/keys](https://openrouter.ai/keys)<br>4. Restart the bot after updating `.env` |

### 429 Rate Limited

| Symptom | Solution |
|---|---|
| Bot responds with `OpenRouter error: 429` | 1. OpenRouter rate limits vary by model and plan<br>2. The client automatically retries with exponential backoff (max 2 retries)<br>3. Switch to a model with higher rate limits<br>4. Reduce `MAX_HISTORY_MESSAGES` to decrease token usage per request |

### Model not found

| Symptom | Solution |
|---|---|
| Bot returns `OpenRouter error: 404` or `RuntimeError` | 1. Model name must use `provider/model` format (e.g., `openai/gpt-4o-mini`)<br>2. Check available models at [openrouter.ai/models](https://openrouter.ai/models)<br>3. Some models require credits — verify the model is free or you have balance |

### Bot token invalid / 401 Unauthorized (Telegram)

| Symptom | Solution |
|---|---|
| Bot fails to start with Telegram `401 Unauthorized` | 1. Check `BOT_TOKEN` in `.env` for typos, missing characters, or extra whitespace<br>2. Regenerate the token via @BotFather (`/token` command)<br>3. Restart the bot after updating `.env` |

### Silent response from bot (whitelist active)

| Symptom | Solution |
|---|---|
| Bot does not respond to your messages | 1. If `ALLOWED_USER_IDS` is set, only listed users can interact<br>2. Messages from other users are silently ignored (logged as `BLOCKED`)<br>3. To open access: set `ALLOWED_USER_IDS=` (empty)<br>4. To find your user ID: message [@userinfobot](https://t.me/userinfobot) |

### Timeout waiting for model response

| Symptom | Solution |
|---|---|
| Bot responds with timeout error or takes very long | 1. Increase `RESPONSE_TIMEOUT` in `.env` (default: 120s)<br>2. Some models are slower — try `openai/gpt-4o-mini` for faster responses<br>3. Reduce `MAX_HISTORY_MESSAGES` to decrease token count |

### ModuleNotFoundError on startup

| Symptom | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'aiogram'` (or similar) | 1. Ensure virtual environment is activated<br>2. Run `pip install -r requirements.txt`<br>3. Verify you're running from the project root directory |

### System prompt not loading

| Symptom | Solution |
|---|---|
| Bot uses default fallback prompt instead of your custom one | 1. Verify `prompts/system.md` exists and is readable<br>2. Check `SYSTEM_PROMPT_PATH` in `.env` points to the correct file<br>3. The bot logs a warning and uses a fallback if the file is missing |

---

## 📁 Project Structure

```
py-tg-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point: Bot, Dispatcher, OpenRouterClient, startup
│   ├── config.py            # AppConfig (pydantic-settings), lru_cached get_config()
│   ├── access.py            # Pure function: is_user_allowed() + log_access_attempt()
│   ├── handlers/
│   │   └── chat.py          # /start + text handler
│   ├── middlewares/
│   │   └── access_middleware.py  # Filters by chat_type and allowed_user_ids
│   └── services/
│       ├── lm_client.py     # Async httpx client for OpenRouter /api/v1/chat/completions
│       └── context_manager.py    # Per-user conversation history with asyncio.Lock
├── utils/
│   └── prompt_loader.py     # load_system_prompt() with lru_cache + fallback
├── prompts/
│   └── system.md            # System prompt (loaded at config init)
├── scripts/
│   ├── verify_setup.py      # Validate .env, OpenRouter connectivity, imports
│   └── test_lm_connection.py    # Test OpenRouter API directly
├── tests/                   # Pytest test suite
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
├── pyproject.toml           # Project metadata and pytest config
└── README.md                # This file
```

---

## 📝 License

[Add your license here]
