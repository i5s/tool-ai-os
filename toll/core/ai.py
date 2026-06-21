"""High-level AI orchestrator.

This module provides a backwards-compatible synchronous interface
for existing CLI and bot code. New code (especially the FastAPI layer)
should prefer using ProviderRegistry directly for async support.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from .limiter import Limiter
from .registry import ProviderRegistry
from .settings import Settings
from .connection_manager import ConnectionManager
from ..core.config import DB_PATH


def _run_async(coro):
    """Safely run a coroutine from a sync context.

    Handles both cases:
    - No running event loop: uses asyncio.run()
    - Running event loop: dispatches to a thread with its own loop
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


class AI:
    """Synchronous facade over the provider registry."""

    def __init__(self, cm: ConnectionManager | None = None):
        m = cm or ConnectionManager(DB_PATH)
        self.settings = Settings(cm=m)
        self.registry = ProviderRegistry(self.settings)
        self.limiter = Limiter(cm=m, settings=self.settings)

    def ask(self, prompt: str, system: str = "", provider_name: str | None = None) -> str:
        if provider_name:
            provider = self.registry.get_llm(provider_name)
            if provider and self.limiter.can_use(provider_name):
                try:
                    response = _run_async(provider.ask(prompt, system))
                    self.limiter.log_usage(provider_name)
                    return response.text
                except Exception:
                    pass
        for name in self.registry.available_llm():
            if not self.limiter.can_use(name):
                continue
            provider = self.registry.get_llm(name)
            try:
                response = _run_async(provider.ask(prompt, system))
                self.limiter.log_usage(name)
                return response.text
            except Exception:
                continue
        raise RuntimeError("كل مزودي AI غير متاحين اليوم (تم استهلاك الـ limit)")

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        provider = self.registry.get_search()
        if hasattr(provider, "search_sync"):
            results = provider.search_sync(query, max_results)
        else:
            results = _run_async(provider.search(query, max_results))
        return [
            {"title": r.title, "url": r.url, "snippet": r.snippet}
            for r in results
        ]

    def limit_status(self):
        return self.limiter.status()

    def provider_status(self):
        return self.registry.status()
