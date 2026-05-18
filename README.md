# Telegram Bot (OpenRouter + LangSearch + aiogram 3)

## 📦 Overview

Telegram bot that connects to cloud LLMs via OpenRouter's OpenAI-compatible API and features automated, background Web Search capabilities using LangSearch API. Built with **aiogram 3.x**, **pydantic-settings**, and **httpx**.

**Features:**
- Real-time Web Search background integration (LangSearch)
- User whitelisting via `ALLOWED_USER_IDS`
- Per-user conversation history with configurable retention
- System prompt loaded from `prompts/system.md` with dynamic datetime and localization injection
- Graceful error handling with retry logic (429/503) and async timeouts
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
| Web Search | LangSearch API |

---

## 🛠 Prerequisites

| Requirement | Version / Details |
|---|---|
| Python | 3.11+ |
| OpenRouter API Key | Get it at [openrouter.ai/keys](https://openrouter.ai/keys) |
| Telegram Bot Token | Obtained from [@BotFather](https://t.me/BotFather) |
| LangSearch API Key | Get it at [langsearch.com](https://langsearch.com) (Optional, for Web Search) |

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

Edit `.env` and set `BOT_TOKEN`, `OPENROUTER_API_KEY`, and `LANGSEARCH_API_KEY`:

```env
BOT_TOKEN=your_telegram_bot_token_here
OPENROUTER_API_KEY=sk-or-v1-your-key-here
LANGSEARCH_API_KEY=your_langsearch_key_here
```

### 5. Run the bot

```bash
python -m bot.main
```

---

## ⚙️ Configuration

All settings are managed via environment variables or a `.env` file. The bot uses `pydantic-settings` for validation.

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `BOT_TOKEN` | `str` | — | **Yes** | Telegram bot token from @BotFather |
| `OPENROUTER_API_KEY` | `str` | — | **Yes** | OpenRouter API key |
| `LANGSEARCH_API_KEY` | `str` | `None` | No | LangSearch API key. If empty, web search is disabled |
| `SEARCH_RESULT_COUNT` | `int` | `5` | No | Number of web pages to retrieve per search |
| `OPENROUTER_BASE_URL` | `str` | `https://openrouter.ai/api/v1` | No | Base URL of the OpenRouter API |
| `OPENROUTER_DEFAULT_MODEL` | `str` | `google/gemma-4-31b-it` | No | Default model in `provider/model` format |
| `ALLOWED_USER_IDS` | `str` | `""` | No | Comma-separated list of allowed Telegram user IDs. **Empty = open access** |
| `SYSTEM_PROMPT_PATH` | `str` | `prompts/system.md` | No | Path to the system prompt markdown file |
| `MAX_HISTORY_MESSAGES` | `int` | `10` | No | Maximum number of messages retained per conversation |
| `MAX_INPUT_LENGTH` | `int` | `4000` | No | Maximum user message length in characters |
| `RESPONSE_TIMEOUT` | `int` | `120` | No | HTTP read/write timeout in seconds for LLM requests |

---

## 🧪 Testing & Quality

### Run all tests

```bash
python -m pytest tests/ -v --tb=short
```

The test suite covers:
- Configuration parsing and edge cases
- Access control validation
- Context manager atomic operations and isolated user queues
- OpenRouter client HTTP status handling, retries, and format validation
- LangSearch client timeouts and JSON handling

### Verify setup (environment + connectivity)

```bash
python -m scripts/verify_setup
```

---

## 🔧 Troubleshooting

### Web Search (LangSearch) not triggering
| Symptom | Solution |
|---|---|
| Bot answers without searching the web | 1. Ensure `LANGSEARCH_API_KEY` is set.<br>2. Check bot logs for `Performing web search for...` or `LangSearch timed out`.<br>3. Search has an 8-second hard timeout to prevent bot lockups. |

### 401/403 Unauthorized (Invalid API Key)
| Symptom | Solution |
|---|---|
| Bot fails with `OpenRouter error: 401` or `403` | 1. Verify `OPENROUTER_API_KEY` in `.env` is correct. |

### 429 Rate Limited
| Symptom | Solution |
|---|---|
| Bot responds with `OpenRouter error: 429` | 1. OpenRouter rate limits vary by model.<br>2. Switch to a model with higher limits. |

### Silent response from bot (whitelist active)
| Symptom | Solution |
|---|---|
| Bot does not respond to your messages | 1. If `ALLOWED_USER_IDS` is set, only listed users can interact.<br>2. To open access: set `ALLOWED_USER_IDS=` (empty). |

---

## 📁 Project Structure

```text
py-tg-bot/
├── bot/
│   ├── main.py              # Entry point: Bot, OpenRouterClient, LangSearchClient
│   ├── config.py            # AppConfig (pydantic-settings)
│   ├── access.py            # is_user_allowed()
│   ├── handlers/
│   │   └── chat.py          # Message handling, Search query generation, date injection
│   ├── middlewares/
│   │   └── access_middleware.py
│   └── services/
│       ├── lm_client.py     # Async client for OpenRouter
│       ├── langsearch_client.py # Async client for LangSearch
│       └── context_manager.py
├── utils/
│   └── prompt_loader.py
├── prompts/
│   ├── system.md
│   └── system-deep4pro.md
├── scripts/
│   ├── verify_setup.py
│   └── test_lm_connection.py
├── tests/                   # 40 Pytest cases
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```
