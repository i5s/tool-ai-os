from toll.core.feature_flags import FeatureFlags
from toll.core.provider_selector import ProviderSelector
from toll.core.registry import ProviderRegistry
from toll.core.settings import Settings


class FakePIE:
    def resolve(self, user_input, media_type="text",
                execution_profile_id="", model_id=None):
        from toll.prompt.engine import PromptPackage
        return PromptPackage(
            prompt=f"Optimized: {user_input}",
            model_id=model_id or "opencode",
            profile_id="product_ad",
            execution_profile_id=execution_profile_id,
            prompt_version=1,
            params={"media_type": media_type},
            debug_info={"intent": "test"},
        )


def test_report_service_pie_enabled(feature_flags, cm):
    from toll.application.report_service import ReportService
    from toll.application.artifact_service import ArtifactService
    feature_flags.enable("prompt_intelligence")
    registry = ProviderRegistry()
    settings = Settings()
    selector = ProviderSelector(registry, settings, feature_flags)
    svc = ReportService(
        ArtifactService(cm), selector, cm,
        flags=feature_flags, prompt_intelligence=FakePIE(),
    )
    assert svc.prompt_intelligence is not None


def test_presentation_service_pie_enabled(feature_flags, cm):
    from toll.application.presentation_service import PresentationService
    from toll.application.artifact_service import ArtifactService
    feature_flags.enable("prompt_intelligence")
    registry = ProviderRegistry()
    settings = Settings()
    selector = ProviderSelector(registry, settings, feature_flags)
    svc = PresentationService(
        ArtifactService(cm), selector, cm,
        flags=feature_flags, prompt_intelligence=FakePIE(),
    )
    assert svc.prompt_intelligence is not None


def test_research_service_pie_enabled(feature_flags, cm):
    from toll.application.research_service import ResearchService
    from toll.application.artifact_service import ArtifactService
    feature_flags.enable("prompt_intelligence")
    registry = ProviderRegistry()
    settings = Settings()
    selector = ProviderSelector(registry, settings, feature_flags)
    svc = ResearchService(
        ArtifactService(cm), selector, cm,
        flags=feature_flags, prompt_intelligence=FakePIE(),
    )
    assert svc.prompt_intelligence is not None


def test_media_service_pie_enabled(feature_flags, cm):
    from toll.application.media_service import MediaService
    feature_flags.enable("prompt_intelligence")
    registry = ProviderRegistry()
    settings = Settings()
    selector = ProviderSelector(registry, settings, feature_flags)
    svc = MediaService(
        cm, registry, selector, feature_flags,
        prompt_intelligence=FakePIE(),
    )
    assert svc.prompt_intelligence is not None


def test_media_service_pie_optimizes_prompt(feature_flags, cm):
    from toll.application.media_service import MediaService
    from toll.ports.media import MediaPort, MediaRequest, MediaResult

    class FakeMedia(MediaPort):
        name = "fake"
        def generate(self, request):
            return MediaResult(success=True, url="https://ex.co/img.png",
                               media_data=b"img", media_type="image",
                               content_type="image/png", file_size_bytes=100)

    feature_flags.enable("prompt_intelligence")
    feature_flags.enable("media_generation")
    registry = ProviderRegistry()
    registry.register_media("fake", FakeMedia())
    settings = Settings()
    selector = ProviderSelector(registry, settings, feature_flags)
    svc = MediaService(cm, registry, selector, feature_flags,
                       prompt_intelligence=FakePIE())
    result = svc.generate({"prompt": "a cat", "media_type": "image"})
    assert result.get("success") is True
