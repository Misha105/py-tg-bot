# Requires dev dependencies: pip install -e ".[dev]" or pip install ruff black mypy pytest-cov

.PHONY: setup run test test-cov verify lint format typecheck check clean

# Cross-platform environment detection
ifeq ($(OS),Windows_NT)
    VENV_PYTHON := .venv/Scripts/python.exe
    VENV_PIP := .venv/Scripts/pip.exe
else
    VENV_PYTHON := .venv/bin/python
    VENV_PIP := .venv/bin/pip
endif

# Create virtual environment, install dependencies, and initialize logs directory
# Note: Uses explicit venv python paths to avoid shell activation quirks in Make
setup:
	python -m venv .venv
	$(VENV_PIP) install -r requirements.txt
	$(VENV_PYTHON) -c "import os; os.makedirs('logs', exist_ok=True)"

# Run the Telegram bot
run:
	$(VENV_PYTHON) -m bot.main

# Run test suite with verbose output and short tracebacks
test:
	$(VENV_PYTHON) -m pytest tests/ -v --tb=short

# Run tests with coverage report (installs pytest-cov if missing)
test-cov:
	$(VENV_PIP) install pytest-cov
	$(VENV_PYTHON) -m pytest --cov=bot --cov-report=term-missing

# Verify environment configuration and LM Studio connectivity
verify:
	$(VENV_PYTHON) -m scripts.verify_setup

# Lint codebase using ruff
lint:
	$(VENV_PYTHON) -m ruff check bot/ tests/ scripts/

# Format codebase using ruff and black
format:
	$(VENV_PYTHON) -m ruff check --fix .
	$(VENV_PYTHON) -m black .

# Run type checking with mypy
typecheck:
	$(VENV_PYTHON) -m mypy bot/ tests/ scripts/

# Run format, lint, and typecheck sequentially
check: format lint typecheck

# Remove generated artifacts, caches, and virtual environment
clean:
	$(VENV_PYTHON) -c "import shutil, os, glob; [shutil.rmtree(d) for d in ['__pycache__', '.pytest_cache', 'htmlcov', 'logs', '.venv'] if os.path.exists(d)]; [os.remove(f) for f in glob.glob('.coverage*') if os.path.exists(f)]"
