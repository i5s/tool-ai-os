from toll.prompt.engine import PromptIntelligenceEngine
from toll.core.registry import ProviderRegistry
from toll.core.settings import Settings
from toll.prompt.repository import PromptProfile, PromptProfileRepository


class FakeContextEngine:
    def build(self, message, recent_messages=None, memory_limit=10,
              message_history_limit=6):
        from toll.context.engine import ContextResult
        return ContextResult(
            prompt=f"Context for: {message}",
            memories=[
                {"type": "brand", "value": "Luxury Dairy Co", "key": "brand_style"},
                {"type": "project", "value": "Q3 Campaign", "key": "campaign"},
            ],
            active_workspace={
                "brand": {"name": "Luxury Dairy Co"},
                "project": {"name": "Q3 Campaign"},
            },
            recent_messages=[{"role": "user", "content": "create an ad"}],
        )


def test_context_is_injected_into_resolve(feature_flags, cm):
    feature_flags.enable("prompt_intelligence_seed")
    registry = ProviderRegistry(Settings())
    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)
    engine.context_engine = FakeContextEngine()
    pkg = engine.resolve("اعلان حليب", media_type="image")
    assert pkg.debug_info["context_keys"] is not None
    assert "active_brand" in str(pkg.debug_info["context_keys"]) or "active_project" in str(pkg.debug_info["context_keys"])


def test_context_engine_is_called(feature_flags, cm):
    feature_flags.enable("prompt_intelligence_seed")
    registry = ProviderRegistry(Settings())
    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)
    engine.context_engine = FakeContextEngine()
    context = engine._gather_context("test prompt", "image")
    assert "active_brand" in context
    assert "active_project" in context
    assert context["active_brand"] == "Luxury Dairy Co"


def test_context_fallback_on_error(feature_flags, cm):
    class BrokenEngine:
        def build(self, *a, **kw):
            raise RuntimeError("broken")

    feature_flags.enable("prompt_intelligence_seed")
    registry = ProviderRegistry(Settings())
    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)
    engine.context_engine = BrokenEngine()
    context = engine._gather_context("test", "image")
    assert context["style"] == "modern"
    assert context["tone"] == "professional"


def test_record_success_called_through_engine(feature_flags, cm):
    feature_flags.enable("prompt_intelligence_seed")
    registry = ProviderRegistry(Settings())
    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)
    repo = PromptProfileRepository(cm)
    repo.create(PromptProfile(id="test:profile", name="Test"))
    engine.record_success("test:profile", "r:model", "a prompt", artifact_id="art:1")
    avg = engine.prompt_memory.get_avg_score("test:profile")
    assert avg is None  # no score recorded, just success without score


def test_record_failure_adds_to_blacklist(feature_flags, cm):
    feature_flags.enable("prompt_intelligence_seed")
    registry = ProviderRegistry(Settings())
    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)
    repo = PromptProfileRepository(cm)
    repo.create(PromptProfile(id="test:bf", name="Blacklist Test"))
    engine.record_failure("test:bf", "bad:model", "timeout")
    assert engine.prompt_memory.is_blacklisted("test:bf", "bad:model") is True


def test_select_model_uses_scores(feature_flags, cm):
    feature_flags.enable("prompt_intelligence_seed")
    registry = ProviderRegistry(Settings())
    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)
    repo = PromptProfileRepository(cm)
    repo.create(PromptProfile(id="test:sc", name="Score Test"))
    engine.prompt_memory.record_success("test:sc", "high:model", "good", score=0.9)
    engine.prompt_memory.record_success("test:sc", "low:model", "bad", score=0.2)
    high_score = engine.prompt_memory.get_avg_score("test:sc", "high:model")
    low_score = engine.prompt_memory.get_avg_score("test:sc", "low:model")
    assert high_score == 0.9
    assert low_score == 0.2
    assert high_score > low_score


def test_select_model_prefers_higher_score(feature_flags, cm):
    feature_flags.enable("prompt_intelligence_seed")
    feature_flags.enable("model_registry_seed")
    from toll.model_registry.service import ModelRegistryService
    registry = ProviderRegistry(Settings())
    mr = ModelRegistryService(cm=cm, flags=feature_flags)
    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry,
                                      model_registry=mr)
    repo = PromptProfileRepository(cm)
    repo.create(PromptProfile(id="test:rank", name="Rank"))
    mr.register({
        "provider": "test", "provider_model_id": "high",
        "name": "High", "media_types": ["image"], "status": "active",
    })
    mr.register({
        "provider": "test", "provider_model_id": "low",
        "name": "Low", "media_types": ["image"], "status": "active",
    })
    models = mr.list(media_type="image", status="active")
    high_m = [m for m in models if "high" in m.id][0]
    low_m = [m for m in models if "low" in m.id][0]
    engine.prompt_memory.record_success("test:rank", high_m.id, "good", score=0.95)
    engine.prompt_memory.record_success("test:rank", low_m.id, "bad", score=0.15)
    from toll.prompt.repository import PromptProfile as PP
    result = engine._select_model(PP(id="test:rank", name="Rank"), media_type="image",
                                  preferred=None)
    assert result == high_m.id
