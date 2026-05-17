"""Quick connection test for LM Studio API."""

import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv


async def main() -> None:
    load_dotenv()

    base_url = os.getenv("LM_STUDIO_BASE_URL", "").rstrip("/")
    api_key = os.getenv("LM_STUDIO_API_KEY")
    model = os.getenv("DEFAULT_MODEL", "gemma-4-e4b-uncensored-hauhaucs-aggressive")

    if not base_url:
        print("❌ LM_STUDIO_BASE_URL is not set in .env")
        sys.exit(1)

    url = f"{base_url}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.5,
    }

    async with httpx.AsyncClient(timeout=10) as client:
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
