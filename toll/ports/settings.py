"""Abstract port for settings sources."""

from abc import ABC, abstractmethod


class SettingsPort(ABC):
    """Port for reading and writing settings."""

    @abstractmethod
    def get(self, key: str, default=None):
        """Get a setting value."""
        ...

    @abstractmethod
    def set(self, key: str, value):
        """Set a setting value."""
        ...

    @abstractmethod
    def all(self) -> dict:
        """Return all settings as a dictionary."""
        ...
