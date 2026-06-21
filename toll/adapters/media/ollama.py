from __future__ import annotations

from ...ports.media import MediaPort, MediaRequest, MediaResult


class OllamaMediaAdapter(MediaPort):
    name = "ollama"

    def is_available(self) -> bool:
        return False

    def supported_types(self) -> list[str]:
        return []

    def generate(self, request: MediaRequest) -> MediaResult:
        return MediaResult(success=False, error="Ollama media generation not yet supported")
