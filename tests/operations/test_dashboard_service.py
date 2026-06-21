from toll.operations.dashboard_service import ProviderDashboardService
from toll.core.registry import ProviderRegistry
from toll.core.settings import Settings


def test_summary_empty(feature_flags, cm):
    registry = ProviderRegistry(Settings())
    svc = ProviderDashboardService(cm, registry)
    result = svc.summary()
    assert isinstance(result, list)
    assert len(result) >= 2  # opencode + ollama


def test_summary_includes_providers(feature_flags, cm):
    registry = ProviderRegistry(Settings())
    svc = ProviderDashboardService(cm, registry)
    result = svc.summary()
    names = {p["name"] for p in result}
    assert "opencode" in names
    assert "ollama" in names


def test_provider_detail_existing(feature_flags, cm):
    registry = ProviderRegistry(Settings())
    svc = ProviderDashboardService(cm, registry)
    detail = svc.provider_detail("opencode")
    assert detail is not None
    assert detail["name"] == "opencode"


def test_provider_detail_missing(feature_flags, cm):
    registry = ProviderRegistry(Settings())
    svc = ProviderDashboardService(cm, registry)
    assert svc.provider_detail("nonexistent") is None


def test_provider_detail_with_model_breakdown(feature_flags, cm):
    registry = ProviderRegistry(Settings())
    svc = ProviderDashboardService(cm, registry)
    detail = svc.provider_detail("opencode")
    assert "model_breakdown" in detail
