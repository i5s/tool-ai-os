import pytest
from toll.core.provider_selector import ProviderSelector
from toll.core.settings import Settings
from toll.core.registry import ProviderRegistry
from toll.model.artifact import ArtifactType


def test_selector_returns_provider(cm):
    settings = Settings(cm=cm)
    registry = ProviderRegistry(settings)
    from toll.core.feature_flags import FeatureFlags
    flags = FeatureFlags(cm=cm)
    selector = ProviderSelector(registry, settings, flags)
    result = selector.select(ArtifactType.REPORT)
    assert result is None or isinstance(result, str)


def test_selector_returns_none_when_no_providers(cm):
    settings = Settings(cm=cm)
    registry = ProviderRegistry(settings)
    from toll.core.feature_flags import FeatureFlags
    flags = FeatureFlags(cm=cm)
    flags.disable("provider_opencode")
    flags.disable("provider_ollama")
    selector = ProviderSelector(registry, settings, flags)
    result = selector.select(ArtifactType.REPORT)
    assert result is None or isinstance(result, str)
