"""Asynchronous client for LangSearch API."""

import logging

import httpx

logger = logging.getLogger(__name__)


class LangSearchClient:
    """Async client for interacting with LangSearch API."""

    def __init__(self, api_key: str, timeout: int = 30) -> None:
        self.api_key = api_key
        self.base_url = "https://api.langsearch.com/v1"
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            base_url=self.base_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()

    async def search(self, query: str, count: int = 5) -> str | None:
        """Perform a web search and return formatted results."""
        if not self.api_key:
            return None

        payload = {"query": query, "freshness": "noLimit", "count": count, "summary": True}

        try:
            response = await self.client.post("/web-search", json=payload)
            response.raise_for_status()
            data = response.json()

            if data.get("code") != 200:
                logger.error("LangSearch API error: %s", data.get("msg"))
                return None

            web_pages = data.get("data", {}).get("webPages", {}).get("value", [])
            if not web_pages:
                return "No search results found."

            results = []
            for i, page in enumerate(web_pages, 1):
                title = page.get("name", "No Title")
                url = page.get("url", "")
                snippet = page.get("summary", page.get("snippet", ""))
                results.append(f"{i}. {title}\nURL: {url}\nSnippet: {snippet}")

            return "\n\n".join(results)

        except httpx.HTTPError as exc:
            logger.error("LangSearch HTTP Error: %s", exc)
            return None
        except Exception as exc:
            logger.error("LangSearch Error: %s", exc)
            return None
