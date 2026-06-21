import pytest
from toll.core.limiter import Limiter
from toll.core.storage import Storage


@pytest.fixture
def limiter(storage: Storage) -> Limiter:
    return Limiter(storage=storage)


def test_can_use_within_limit(limiter: Limiter, storage: Storage):
    storage.set_config("daily_limit_opencode", "5")
    assert limiter.can_use("opencode") is True


def test_can_use_exceeds_limit(limiter: Limiter, storage: Storage):
    storage.set_config("daily_limit_opencode", "2")
    storage.log_usage("opencode")
    storage.log_usage("opencode")
    assert limiter.can_use("opencode") is False


def test_remaining_decreases_with_usage(limiter: Limiter, storage: Storage):
    storage.set_config("daily_limit_opencode", "5")
    assert limiter.remaining("opencode") == 5
    storage.log_usage("opencode")
    assert limiter.remaining("opencode") == 4


def test_status_includes_all_providers(limiter: Limiter):
    status = limiter.status()
    for provider in ["opencode", "ollama", "browser"]:
        assert provider in status
        assert "can_use" in status[provider]
        assert "remaining" in status[provider]
