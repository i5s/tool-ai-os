from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class MediaStorage(ABC):
    @abstractmethod
    def save(self, data: bytes, media_type: str, extension: str) -> str:
        ...

    @abstractmethod
    def get_path(self, storage_key: str) -> Path | None:
        ...

    @abstractmethod
    def delete(self, storage_key: str) -> bool:
        ...
