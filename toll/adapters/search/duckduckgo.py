"""DuckDuckGo Lite search adapter.

Uses DuckDuckGo Lite HTML interface. No API key required.
"""

import re
import urllib.parse
import httpx

from ...ports.search import SearchPort, SearchResult


class DuckDuckGoSearch(SearchPort):
    name = "duckduckgo"

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.base_url = "https://lite.duckduckgo.com/lite/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    def is_available(self) -> bool:
        return True  # No API key required

    def _fetch(self, query: str) -> str:
        data = {"q": query, "kl": "wt-wt"}
        with httpx.Client(
            timeout=self.timeout, follow_redirects=True, headers=self.headers
        ) as client:
            response = client.post(self.base_url, data=data)
            response.raise_for_status()
            return response.text

    async def _fetch_async(self, query: str) -> str:
        data = {"q": query, "kl": "wt-wt"}
        async with httpx.AsyncClient(
            timeout=self.timeout, follow_redirects=True, headers=self.headers
        ) as client:
            response = await client.post(self.base_url, data=data)
            response.raise_for_status()
            return response.text

    def _parse(self, html: str, max_results: int) -> list[SearchResult]:
        results = []
        # Find each result block: result-link + optional result-snippet
        link_pattern = re.compile(
            r"<a\s+(?:[^>]*\s+)?href=['\"]([^'\"]+)['\"][^>]*class=['\"]result-link['\"][^>]*>(.*?)</a>",
            re.IGNORECASE | re.DOTALL,
        )
        # Fallback: class before href
        link_pattern_alt = re.compile(
            r"<a\s+(?:[^>]*\s+)?class=['\"]result-link['\"][^>]*href=['\"]([^'\"]+)['\"][^>]*>(.*?)</a>",
            re.IGNORECASE | re.DOTALL,
        )
        snippet_pattern = re.compile(
            r"<td[^>]+class=['\"]result-snippet['\"][^>]*>(.*?)</td>",
            re.IGNORECASE | re.DOTALL,
        )

        links = list(link_pattern.finditer(html))
        if not links:
            links = list(link_pattern_alt.finditer(html))
        snippets = snippet_pattern.findall(html)

        for idx, match in enumerate(links[:max_results]):
            url = urllib.parse.unquote(match.group(1))
            title = self._strip_html(match.group(2))
            snippet = self._strip_html(snippets[idx]) if idx < len(snippets) else ""

            if url.startswith("//"):
                url = "https:" + url

            results.append(SearchResult(title=title, url=url, snippet=snippet))

        return results

    @staticmethod
    def _strip_html(text: str) -> str:
        text = re.sub(r"<[^>]+>", "", text)
        return (
            text.replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
            .strip()
        )

    def search_sync(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Synchronous version for use from sync callers."""
        html = self._fetch(query)
        return self._parse(html, max_results)

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        html = await self._fetch_async(query)
        return self._parse(html, max_results)
