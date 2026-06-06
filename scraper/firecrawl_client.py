from __future__ import annotations

from typing import Any

from config.settings import get_settings


class FirecrawlScraper:
    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.firecrawl_api_key
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY is required")

        from firecrawl import FirecrawlApp

        self._app = FirecrawlApp(api_key=self.api_key)

    def scrape(self, url: str) -> str:
        try:
            result = self._app.scrape_url(url, formats=["markdown", "html"])
        except TypeError:
            result = self._app.scrape_url(url, params={"formats": ["markdown", "html"]})
        return _extract_content(result)


def _extract_content(result: Any) -> str:
    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        for key in ("html", "markdown", "content"):
            value = result.get(key)
            if value:
                return str(value)

        data = result.get("data")
        if isinstance(data, dict):
            for key in ("html", "markdown", "content"):
                value = data.get(key)
                if value:
                    return str(value)

    for key in ("html", "markdown", "content"):
        value = getattr(result, key, None)
        if value:
            return str(value)

    raise ValueError("Firecrawl response did not contain markdown/html content")
