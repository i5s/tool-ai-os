import pytest

from toll.application.media_service import MediaService
from toll.core.provider_selector import ProviderSelector
from toll.core.registry import ProviderRegistry
from toll.core.settings import Settings
from toll.ports.media import MediaPort, MediaRequest, MediaResult


class FakeMediaAdapter(MediaPort):
    name = "fake"

    def generate(self, request: MediaRequest) -> MediaResult:
        if "fail" in request.prompt:
            return MediaResult(success=False, error="Fake failure")
        return MediaResult(
            success=True,
            url="https://fake.example/img.png",
            media_data=b"fake-image-bytes",
            media_type=request.media_type,
            content_type="image/png",
            file_size_bytes=16,
        )


def _make_registry():
    r = ProviderRegistry()
    r.register_media("fake", FakeMediaAdapter())
    return r


def _make_svc(feature_flags, cm, registry=None):
    r = registry or _make_registry()
    settings = Settings()
    selector = ProviderSelector(r, settings, feature_flags)
    return MediaService(cm=cm, registry=r, selector=selector, flags=feature_flags)


def test_generate_no_prompt(feature_flags, cm):
    svc = _make_svc(feature_flags, cm)
    result = svc.generate({"prompt": "", "media_type": "image"})
    assert result["success"] is False
    assert "No prompt" in result["error"]


def test_generate_disabled_flag(feature_flags, cm):
    feature_flags.disable("media_generation")
    svc = _make_svc(feature_flags, cm)
    result = svc.generate({"prompt": "hello", "media_type": "image"})
    assert result["success"] is False
    assert "disabled" in result["error"].lower()


def test_generate_video_disabled_by_default(feature_flags, cm):
    svc = _make_svc(feature_flags, cm)
    result = svc.generate({"prompt": "hello", "media_type": "video"})
    assert result["success"] is False
    assert "disabled" in result["error"].lower()


def test_generate_success(feature_flags, cm):
    svc = _make_svc(feature_flags, cm)
    result = svc.generate({"prompt": "test image", "media_type": "image"})
    assert result["success"] is True
    assert result["media_type"] == "image"
    assert result["content_type"] == "image/png"


def test_generate_adapter_failure(feature_flags, cm):
    svc = _make_svc(feature_flags, cm)
    result = svc.generate({"prompt": "fail", "media_type": "image"})
    assert result["success"] is False
    assert "Fake failure" in result["error"]


def test_generate_no_available_provider(feature_flags, cm):
    r = ProviderRegistry()
    settings = Settings()
    selector = ProviderSelector(r, settings, feature_flags)
    svc = MediaService(cm=cm, registry=r, selector=selector, flags=feature_flags)
    result = svc.generate({"prompt": "test", "media_type": "image"})
    assert result["success"] is False
    assert "No media provider" in result["error"]


def test_generate_with_provider_model_id(feature_flags, cm):
    svc = _make_svc(feature_flags, cm)
    result = svc.generate({
        "prompt": "test",
        "media_type": "image",
        "provider": "fake",
        "provider_model_id": "fake:test",
    })
    assert result["success"] is True


def test_generate_returns_artifact_id(feature_flags, cm):
    svc = _make_svc(feature_flags, cm)
    result = svc.generate({"prompt": "test", "media_type": "image"})
    assert result["success"] is True
    assert len(result["artifact_id"]) > 0
