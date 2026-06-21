from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseRenderer(ABC):
    @abstractmethod
    def render(self, title: str, content: Any) -> str:
        ...
