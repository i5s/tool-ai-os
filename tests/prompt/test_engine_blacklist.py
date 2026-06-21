from toll.prompt.engine import PromptIntelligenceEngine
from toll.core.registry import ProviderRegistry
from toll.core.settings import Settings
from toll.prompt.repository import PromptProfile, PromptProfileRepository


def test_blacklist_skips_blacklisted_model(feature_flags, cm):
    feature_flags.enable("prompt_intelligence_seed")
    registry = ProviderRegistry(Settings())

    repo = PromptProfileRepository(cm)
    repo.create(PromptProfile(
        id="test:profile", name="Test",
        media_types=["image"], template="Show {subject}",
    ))

    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)
    engine.prompt_memory.record_failure("test:profile", "blacklisted:model", "test")

    result = engine._select_model(
        PromptProfile(id="test:p", name="P"),
        media_type="image",
        preferred=None,
    )
    assert result is None or result != "blacklisted:model"


def test_blacklist_allows_non_blacklisted(feature_flags, cm):
    feature_flags.enable("prompt_intelligence_seed")
    registry = ProviderRegistry(Settings())

    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)

    result = engine._select_model(
        PromptProfile(id="test:p", name="P"),
        media_type="image",
        preferred="custom:good",
    )
    assert result == "custom:good"
