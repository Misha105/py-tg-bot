"""Environment and project setup verification script."""

import importlib
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)

TOKEN_PATTERN = re.compile(r"^\d+:[A-Za-z0-9_-]+$")
API_KEY_PATTERN = re.compile(r"^sk(-or)?-.+")

MODULES_TO_CHECK = [
    "aiogram",
    "bot.config",
    "bot.main",
    "bot.access",
    "bot.services.lm_client",
    "bot.services.langsearch_client",
    "bot.services.context_manager",
]


def check_env() -> tuple[list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    env_file = PROJECT_ROOT / ".env"

    if not env_file.exists():
        issues.append(".env file not found. Copy .env.example to .env and configure it.")
        return issues, warnings

    env_content = env_file.read_text(encoding="utf-8")
    env_vars = {}
    for line in env_content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env_vars[key.strip()] = value.strip()

    bot_token = env_vars.get("BOT_TOKEN", "")
    if not bot_token:
        issues.append("BOT_TOKEN is empty in .env")
    elif not TOKEN_PATTERN.match(bot_token):
        issues.append("BOT_TOKEN does not match expected format (digits:alphanumeric)")

    api_key = env_vars.get("OPENROUTER_API_KEY", "")
    if not api_key:
        issues.append("OPENROUTER_API_KEY is empty in .env")
    elif not API_KEY_PATTERN.match(api_key):
        issues.append("OPENROUTER_API_KEY must start with sk- or sk-or-")

    langsearch_key = env_vars.get("LANGSEARCH_API_KEY", "")
    if not langsearch_key:
        warnings.append("LANGSEARCH_API_KEY is empty. Web search functionality will be disabled.")

    base_url = env_vars.get("OPENROUTER_BASE_URL", "").rstrip("/")
    if not base_url:
        issues.append("OPENROUTER_BASE_URL is empty in .env")
    elif not base_url.startswith("https://"):
        issues.append("OPENROUTER_BASE_URL must use https scheme")

    return issues, warnings


def check_openrouter(api_key: str) -> tuple[bool, str]:
    url = "https://openrouter.ai/api/v1/models"
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("Authorization", f"Bearer {api_key}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = int(resp.status)
            if status == 200:
                return True, "API key valid. Server responding."
            return False, f"Unexpected status: {status}"
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return False, f"API key rejected. Status: {exc.code}"
        return False, f"OpenRouter server error. Status: {exc.code}"
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return False, f"OpenRouter unreachable: {exc}"


def check_imports() -> list[tuple[str, bool, str]]:
    results = []
    for module_name in MODULES_TO_CHECK:
        try:
            importlib.import_module(module_name)
            results.append((module_name, True, ""))
        except Exception as exc:
            results.append((module_name, False, str(exc)))
    return results


def main() -> None:
    print("=" * 50)
    print("  Setup Verification")
    print("=" * 50)

    has_issues = False

    print("\n[1/3] Checking .env file...")
    env_issues, env_warnings = check_env()

    if not env_issues and not env_warnings:
        print("✅ .env: Valid")

    if env_warnings:
        for warning in env_warnings:
            print(f"⚠️ {warning}")

    if env_issues:
        has_issues = True
        for issue in env_issues:
            print(f"❌ {issue}")

    print("\n[2/3] Checking OpenRouter connectivity...")
    env_file = PROJECT_ROOT / ".env"
    api_key = ""
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("OPENROUTER_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
                break

    if not api_key:
        has_issues = True
        print("❌ OPENROUTER_API_KEY not found in .env")
    else:
        success, message = check_openrouter(api_key)
        if success:
            print(f"✅ OpenRouter: {message}")
        else:
            has_issues = True
            print(f"❌ OpenRouter: {message}")

    print("\n[3/3] Checking project imports...")
    import_results = check_imports()
    for module_name, success, error in import_results:
        if success:
            print(f"✅ Imported: {module_name}")
        else:
            has_issues = True
            print(f"❌ Import failed: {module_name} ({error})")

    print("\n" + "=" * 50)
    if has_issues:
        print("⚠️ Please fix the issues above before starting the bot.")
    else:
        print("🚀 Setup verification complete. Project is ready to run.")
    print("=" * 50)

    sys.exit(1 if has_issues else 0)


if __name__ == "__main__":
    main()
