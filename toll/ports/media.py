from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MediaRequest:
    prompt: str
    media_type: str
    provider_model_id: str = ""
    provider: str = ""
    negative_prompt: str = ""
    size: str | None = None
    duration: int | None = None
    seed: int | None = None
    input_media_path: str | None = None
    style: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class MediaResult:
    success: bool
    url: str = ""
    media_data: bytes | None = None
    media_path: str | None = None
    media_type: str = ""
    provider: str = ""
    provider_model_id: str = ""
    duration_ms: int = 0
    content_type: str = ""
    width: int | None = None
    height: int | None = None
    file_size_bytes: int = 0
    seed: int | None = None
    error: str | None = None
    raw_response: dict = field(default_factory=dict)


class MediaPort(ABC):
    name: str = "abstract_media"

    @abstractmethod
    def generate(self, request: MediaRequest) -> MediaResult:
        ...

    def is_available(self) -> bool:
        return True

    def supported_types(self) -> list[str]:
        return ["image"]
