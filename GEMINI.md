# Project Overview

This is a Telegram bot built with Python and the `aiogram` 3.x framework. It connects to Large Language Models (LLMs) via the OpenRouter API and can perform web searches using the LangSearch API.

The bot is designed to be asynchronous, using `httpx` for non-blocking HTTP requests to external services. Configuration is managed via environment variables and a `.env` file, validated by `pydantic-settings`.

Key features include:
- Whitelisting users based on their Telegram ID.
- Maintaining conversation history for each user.
- Loading a customizable system prompt from a file.
- Code quality is enforced using `ruff`, `black`, and `mypy`.

## Key Files

- **`bot/main.py`**: The main entry point of the application. It initializes the bot, dispatcher, and clients for OpenRouter and LangSearch.
- **`bot/config.py`**: Defines the application's configuration using `pydantic-settings`.
- **`bot/handlers/chat.py`**: Contains the core logic for handling incoming messages from users.
- **`bot/services/lm_client.py`**: An asynchronous client for interacting with the OpenRouter API.
- **`bot/services/langsearch_client.py`**: An asynchronous client for the LangSearch API.
- **`bot/services/context_manager.py`**: Manages the conversation history for each user.
- **`prompts/system.md`**: The default system prompt used to instruct the LLM.
- **`requirements.txt`**: Lists the Python dependencies for the project.
- **`pyproject.toml`**: Project metadata and configuration for build tools, `ruff`, `black`, and `mypy`.
- **`Makefile`**: Contains convenient shortcuts for common development tasks.

## Key Commands

- **`pip install -r requirements.txt`**: Install the required Python dependencies.
- **`python -m bot.main`** or **`make run`**: Start the bot.
- **`make test`**: Run the test suite using `pytest`.
- **`make check`**: Run all code quality checks (formatting, linting, and type checking).
- **`make format`**: Format the code using `ruff` and `black`.
- **`make lint`**: Lint the code with `ruff`.
- **`make typecheck`**: Perform static type checking with `mypy`.
- **`make verify`**: Run a script to verify the environment setup and connectivity to external services.
