"""FastAPI dependency injection providers.

Dependencies share a single ConnectionManager from app.state
to avoid SQLite thread-safety issues in single-user local mode.
"""

from fastapi import Request
from toll.core.connection_manager import ConnectionManager
from toll.core.settings import Settings
from toll.core.registry import ProviderRegistry
from toll.core.feature_flags import FeatureFlags
from toll.core.storage import Storage


def get_connection_manager(request: Request) -> ConnectionManager:
    return request.app.state.cm


def get_storage(request: Request) -> Storage:
    return Storage(cm=request.app.state.cm)


def get_settings(request: Request) -> Settings:
    return Settings(cm=request.app.state.cm)


def get_registry(request: Request) -> ProviderRegistry:
    return ProviderRegistry(Settings(cm=request.app.state.cm))


def get_feature_flags(request: Request) -> FeatureFlags:
    return FeatureFlags(cm=request.app.state.cm)
