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
URL_PATTERN = re.compile(r"^https?://")

MODULES_TO_CHECK = [
    "aiogram",
    "bot.config",
    "bot.main",
    "bot.access",
    "bot.services.lm_client",
    "bot.services.context_manager",
]


def check_env() -> list[str]:
    issues = []
    env_file = PROJECT_ROOT / ".env"

    if not env_file.exists():
        issues.append(".env file not found. Copy .env.example to .env and configure it.")
        return issues

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

    base_url = env_vars.get("LM_STUDIO_BASE_URL", "").rstrip("/")
    if not base_url:
        issues.append("LM_STUDIO_BASE_URL is empty in .env")
    elif not URL_PATTERN.match(base_url):
        issues.append("LM_STUDIO_BASE_URL must start with http:// or https://")

    return issues


def check_lm_studio(base_url: str) -> bool:
    url = f"{base_url}/models"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return int(resp.status) == 200
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError):
        return False


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
    env_issues = check_env()
    if not env_issues:
        print("✅ .env: Valid")
    else:
        has_issues = True
        for issue in env_issues:
            print(f"❌ {issue}")

    print("\n[2/3] Checking LM Studio connectivity...")
    env_file = PROJECT_ROOT / ".env"
    base_url = "http://localhost:1234/v1"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("LM_STUDIO_BASE_URL="):
                base_url = line.split("=", 1)[1].strip().rstrip("/")
                break

    if check_lm_studio(base_url):
        print(f"✅ LM Studio: Online. Server responding at {base_url}")
    else:
        has_issues = True
        print(
            "❌ LM Studio: Unreachable or misconfigured. Ensure server is running on specified port."
        )

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
