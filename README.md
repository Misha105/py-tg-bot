# Local LLM Telegram Bot (LM Studio + aiogram 3)

## 📦 Overview

Telegram bot that connects to a locally running LLM via LM Studio's OpenAI-compatible API. Built with **aiogram 3.x**, **pydantic-settings**, and **httpx**.

**Features:**
- User whitelisting via `ALLOWED_USER_IDS`
- Per-user conversation history with configurable retention
- System prompt loaded from `prompts/system.md`
- Graceful error handling and access logging
- Async architecture with `asyncio.Lock` for thread-safe context management

**Stack:**
| Component | Technology |
|---|---|
| Framework | aiogram 3.x |
| Config | pydantic-settings + python-dotenv |
| HTTP Client | httpx (async) |
| Testing | pytest + pytest-asyncio |
| LLM Backend | LM Studio (OpenAI-compatible API) |

---

## 🛠 Prerequisites

| Requirement | Version / Details |
|---|---|
| Python | 3.11+ |
| LM Studio | Installed and running with OpenAI-compatible server enabled on port 1234 |
| Telegram Bot Token | Obtained from [@BotFather](https://t.me/BotFather) |

> **Important:** LM Studio must have its local server started **before** launching the bot. Open LM Studio, load a model, and click **Start Server** (default: `http://localhost:1234/v1`).

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

### 4. Configure environment

```bash
# Linux / macOS
cp .env.example .env

# Windows (Command Prompt)
copy .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

Edit `.env` and set at least `BOT_TOKEN`:

```env
BOT_TOKEN=your_telegram_bot_token_here
```

### 5. Start LM Studio

1. Open LM Studio
2. Load your preferred model
3. Navigate to the **Server** tab
4. Click **Start Server** (ensure it listens on `http://localhost:1234`)

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
| `LM_STUDIO_BASE_URL` | `str` | `http://localhost:1234/v1` | No | Base URL of the LM Studio API server (trailing slash stripped automatically) |
| `LM_STUDIO_API_KEY` | `str` | `""` | No | API key for LM Studio (leave empty if not required) |
| `ALLOWED_USER_IDS` | `str` | `""` | No | Comma-separated list of allowed Telegram user IDs. **Empty = open access** |
| `SYSTEM_PROMPT_PATH` | `str` | `prompts/system.md` | No | Path to the system prompt markdown file |
| `DEFAULT_MODEL` | `str` | `gemma-4-e4b-uncensored-hauhaucs-aggressive` | No | Default model name used for chat completions |
| `MAX_HISTORY_MESSAGES` | `int` | `10` | No | Maximum number of messages retained per conversation |
| `RESPONSE_TIMEOUT` | `int` | `120` | No | HTTP timeout in seconds for LLM requests |

> **Note on `SYSTEM_PROMPT`:** The system prompt is **not** stored in `.env`. It is loaded from the file specified in `SYSTEM_PROMPT_PATH` (default: `prompts/system.md`) via `@model_validator(mode="after")`. Edit that file directly to customize the bot's behavior.

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

### Test LM Studio connection directly

```bash
python -m scripts/test_lm_connection
```

### Test configuration notes

- `pytest-asyncio` is configured with `asyncio_mode = "auto"` — no `@pytest.mark.asyncio` decorator needed
- Tests must **not** depend on LM Studio or Telegram API
- Use `monkeypatch.setenv()` for config tests, not `.env` file manipulation
- Call `get_config.cache_clear()` before creating `AppConfig` instances in tests

---

## 🔧 Troubleshooting

### ConnectionRefused to LM Studio

| Symptom | Solution |
|---|---|
| `ConnectionRefusedError` or timeout when bot tries to reach LM Studio | 1. Ensure LM Studio is running<br>2. Click **Start Server** in the LM Studio UI<br>3. Verify `LM_STUDIO_BASE_URL` in `.env` matches the server address<br>4. Test manually: `python -m scripts/test_lm_connection` |

### Bot token invalid / 401 Unauthorized

| Symptom | Solution |
|---|---|
| Bot fails to start with `401 Unauthorized` or `invalid token` error | 1. Check `BOT_TOKEN` in `.env` for typos, missing characters, or extra whitespace<br>2. Regenerate the token via @BotFather (`/token` command)<br>3. Restart the bot after updating `.env` |

### Silent response from bot (whitelist active)

| Symptom | Solution |
|---|---|
| Bot does not respond to your messages | 1. If `ALLOWED_USER_IDS` is set, only listed users can interact<br>2. Messages from other users are silently ignored (logged as `BLOCKED`)<br>3. To open access: set `ALLOWED_USER_IDS=` (empty)<br>4. To find your user ID: message [@userinfobot](https://t.me/userinfobot) |

### Timeout waiting for model response

| Symptom | Solution |
|---|---|
| Bot responds with timeout error or takes very long | 1. Increase `RESPONSE_TIMEOUT` in `.env` (default: 120s)<br>2. Ensure the model is **loaded** in LM Studio (not unloaded)<br>3. Use a smaller model or reduce `MAX_HISTORY_MESSAGES`<br>4. Check system resources (RAM/CPU) — local LLMs are resource-intensive |

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
│   ├── main.py              # Entry point: Bot, Dispatcher, LMStudioClient, startup
│   ├── config.py            # AppConfig (pydantic-settings), lru_cached get_config()
│   ├── access.py            # Pure function: is_user_allowed() + log_access_attempt()
│   ├── handlers/
│   │   └── chat.py          # /start + text handler
│   ├── middlewares/
│   │   └── access_middleware.py  # Filters by chat_type and allowed_user_ids
│   └── services/
│       ├── lm_client.py     # Async httpx client for LM Studio /chat/completions
│       └── context_manager.py    # Per-user conversation history with asyncio.Lock
├── utils/
│   └── prompt_loader.py     # load_system_prompt() with lru_cache + fallback
├── prompts/
│   └── system.md            # System prompt (loaded at config init)
├── scripts/
│   ├── verify_setup.py      # Validate .env, LM Studio connectivity, imports
│   └── test_lm_connection.py    # Test LM Studio API directly
├── tests/                   # Pytest test suite
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
├── pyproject.toml           # Project metadata and pytest config
└── README.md                # This file
```

---

## 📝 License

[Add your license here]
