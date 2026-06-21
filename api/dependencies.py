"""FastAPI dependency injection providers.

Dependencies create fresh instances per request to avoid SQLite
thread-safety issues in single-user local mode.
"""

from toll.core.settings import Settings
from toll.core.registry import ProviderRegistry
from toll.core.feature_flags import FeatureFlags


def get_settings() -> Settings:
    """Return a fresh Settings instance per request."""
    return Settings()


def get_registry() -> ProviderRegistry:
    """Return a fresh ProviderRegistry instance per request."""
    return ProviderRegistry(get_settings())


def get_feature_flags() -> FeatureFlags:
    """Return a fresh FeatureFlags instance per request."""
    return FeatureFlags()
