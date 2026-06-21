"""Browser automation placeholder.

Browser automation is NOT in Sprint 1 scope.
Search functionality has moved to toll.adapters.search.
This module is reserved for future browser-based providers.
"""


class BrowserAI:
    """Reserved for future browser automation."""

    def ask(self, prompt: str, url: str = None) -> str:
        raise NotImplementedError("Browser automation is not implemented in V1")

    def get(self, url: str) -> str:
        raise NotImplementedError("Browser automation is not implemented in V1")
