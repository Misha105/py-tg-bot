"""Quick connection test for OpenRouter API."""

import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv


async def main() -> None:
    load_dotenv()

    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_DEFAULT_MODEL", "google/gemma-4-31b-it")

    if not api_key:
        print("❌ OPENROUTER_API_KEY is not set in .env")
        sys.exit(1)

    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.0,
        "max_completion_tokens": 256,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            print(f"✅ Connection successful. Response: {content[:100]}")
        except httpx.RequestError as exc:
            print(f"❌ Connection failed: {type(exc).__name__} - {exc}")
        except httpx.HTTPStatusError as exc:
            print(
                f"❌ Connection failed: HTTP {exc.response.status_code} - {exc.response.text[:200]}"
            )
        except (KeyError, IndexError) as exc:
            print(f"❌ Connection failed: Invalid response format - {exc}")


if __name__ == "__main__":
    asyncio.run(main())
