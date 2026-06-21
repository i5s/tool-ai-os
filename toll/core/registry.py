"""Provider Registry.

Responsibilities:
- Provider discovery
- Provider selection
- Future provider routing
"""

from __future__ import annotations

from ..ports.llm import LLMProvider
from ..ports.search import SearchPort
from ..adapters.llm.opencode import OpenCodeProvider
from ..adapters.llm.ollama import OllamaProvider
from ..adapters.search.duckduckgo import DuckDuckGoSearch
from .settings import Settings


class ProviderRegistry:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self._llm: dict[str, LLMProvider] = {}
        self._search: dict[str, SearchPort] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register_llm("opencode", OpenCodeProvider(self.settings))
        self.register_llm("ollama", OllamaProvider(self.settings))
        self.register_search("duckduckgo", DuckDuckGoSearch())

    def register_llm(self, name: str, provider: LLMProvider):
        self._llm[name] = provider

    def register_search(self, name: str, provider: SearchPort):
        self._search[name] = provider

    def available_llm(self) -> list[str]:
        return [name for name, provider in self._llm.items() if provider.is_available()]

    def available_search(self) -> list[str]:
        return [name for name, provider in self._search.items() if provider.is_available()]

    def all_llm(self) -> dict[str, LLMProvider]:
        return dict(self._llm)

    def all_search(self) -> dict[str, SearchPort]:
        return dict(self._search)

    def get_llm(self, name: str | None = None) -> LLMProvider:
        """Get an LLM provider by name, or fall back to first available."""
        if name:
            provider = self._llm.get(name)
            if provider and provider.is_available():
                return provider
            raise RuntimeError(f"LLM provider '{name}' is not available")

        for fallback in ["opencode", "ollama"]:
            provider = self._llm.get(fallback)
            if provider and provider.is_available():
                return provider

        raise RuntimeError("No LLM provider available")

    def get_search(self, name: str | None = None) -> SearchPort:
        """Get a search provider by name, or fall back to first available."""
        if name:
            provider = self._search.get(name)
            if provider and provider.is_available():
                return provider
            raise RuntimeError(f"Search provider '{name}' is not available")

        for provider in self._search.values():
            if provider.is_available():
                return provider

        raise RuntimeError("No search provider available")

    def status(self) -> dict:
        return {
            "llm": {
                name: provider.is_available()
                for name, provider in self._llm.items()
            },
            "search": {
                name: provider.is_available()
                for name, provider in self._search.items()
            },
        }
