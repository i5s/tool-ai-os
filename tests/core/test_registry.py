import pytest
from toll.core.registry import ProviderRegistry
from toll.core.settings import Settings


@pytest.fixture
def registry(storage):
    settings = Settings(storage=storage)
    return ProviderRegistry(settings=settings)


def test_registry_has_default_providers(registry):
    assert "opencode" in registry.all_llm()
    assert "ollama" in registry.all_llm()
    assert "duckduckgo" in registry.all_search()


def test_registry_lists_available_providers(registry):
    llm = registry.available_llm()
    search = registry.available_search()
    assert isinstance(llm, list)
    assert isinstance(search, list)
    assert "duckduckgo" in search


def test_registry_status_includes_categories(registry):
    status = registry.status()
    assert "llm" in status
    assert "search" in status
