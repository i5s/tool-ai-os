"""Abstract ports for persistence repositories."""

from abc import ABC, abstractmethod


class ConfigRepository(ABC):
    """Port for configuration storage."""

    @abstractmethod
    def get(self, key: str, default=None):
        ...

    @abstractmethod
    def set(self, key: str, value):
        ...


class UsageRepository(ABC):
    """Port for usage tracking."""

    @abstractmethod
    def log(self, provider: str, action: str):
        ...

    @abstractmethod
    def count_today(self, provider: str) -> int:
        ...
