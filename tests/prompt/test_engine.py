from toll.prompt.engine import PromptIntelligenceEngine
from toll.core.registry import ProviderRegistry
from toll.core.settings import Settings


def test_resolve_returns_package(feature_flags, cm):
    feature_flags.enable("prompt_intelligence")
    feature_flags.enable("prompt_intelligence_seed")
    registry = ProviderRegistry(Settings())
    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)
    pkg = engine.resolve("اعلان حليب فاخر", media_type="image")
    assert pkg.prompt is not None
    assert len(pkg.prompt) > 0
    assert "حليب" in pkg.prompt or "subject" not in pkg.prompt


def test_resolve_detects_intent(feature_flags, cm):
    feature_flags.enable("prompt_intelligence_seed")
    registry = ProviderRegistry(Settings())
    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)
    pkg = engine.resolve("video commercial for car", media_type="video")
    assert pkg.profile_id == "video_ad"


def test_resolve_food_intent(feature_flags, cm):
    feature_flags.enable("prompt_intelligence_seed")
    registry = ProviderRegistry(Settings())
    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)
    pkg = engine.resolve("تصوير كيكة شوكولاتة", media_type="image")
    assert pkg.profile_id == "food_photography"


def test_resolve_with_execution_profile(feature_flags, cm):
    feature_flags.enable("prompt_intelligence_seed")
    registry = ProviderRegistry(Settings())
    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)
    pkg = engine.resolve("new product launch", media_type="image",
                         execution_profile_id="marketing")
    assert pkg.execution_profile_id == "marketing"
    assert pkg.profile_id in ("product_ad", "social_media")


def test_resolve_respects_model_preference(feature_flags, cm):
    feature_flags.enable("prompt_intelligence_seed")
    registry = ProviderRegistry(Settings())
    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)
    pkg = engine.resolve("test", media_type="image", model_id="custom:model")
    assert pkg.model_id == "custom:model"


def test_fallback_for_unmatched_intent(feature_flags, cm):
    feature_flags.enable("prompt_intelligence_seed")
    registry = ProviderRegistry(Settings())
    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)
    pkg = engine.resolve("zzzxxxyyy unknown", media_type="image")
    assert pkg.profile_id is not None
    assert len(pkg.prompt) > 0


def test_render_template_replaces_variables(feature_flags, cm):
    registry = ProviderRegistry(Settings())
    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)
    result = engine._render_template("Show {subject} in {style} style",
                                     {"subject": "coffee", "style": "modern"})
    assert result == "Show coffee in modern style"


def test_render_template_partial_variables(feature_flags, cm):
    registry = ProviderRegistry(Settings())
    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)
    result = engine._render_template("Show {subject} in {style} style",
                                     {"subject": "coffee"})
    assert "{style}" in result


def test_detect_intent_arabic(feature_flags, cm):
    registry = ProviderRegistry(Settings())
    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)
    assert engine._detect_intent("ابا اعلان") == "product_ad"
    assert engine._detect_intent("بحث علمي") == "research_report"
    assert engine._detect_intent("عرض تقديمي") == "presentation"


def test_detect_intent_english(feature_flags, cm):
    registry = ProviderRegistry(Settings())
    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)
    assert engine._detect_intent("food photography") == "food_photography"
    assert engine._detect_intent("travel poster") == "travel_poster"
    assert engine._detect_intent("logo design") == "logo_design"


def test_package_includes_debug_info(feature_flags, cm):
    feature_flags.enable("prompt_intelligence_seed")
    registry = ProviderRegistry(Settings())
    engine = PromptIntelligenceEngine(cm=cm, flags=feature_flags, registry=registry)
    pkg = engine.resolve("test prompt", media_type="image")
    assert "intent" in pkg.debug_info
    assert "profile" in pkg.debug_info
