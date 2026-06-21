from toll.engine.renderers.media_renderer import MediaPreviewRenderer
from toll.model.artifact import Artifact, ArtifactStatus, ArtifactType


def _make_image_artifact(**kw):
    defaults = dict(
        id="test-img",
        type=ArtifactType.IMAGE_GEN,
        title="Generated Image",
        status=ArtifactStatus.COMPLETED,
        version=1,
        content={
            "media_url": "https://example.com/img.png",
            "provider": "replicate",
            "model": "replicate:flux-schnell",
            "prompt": "a cat on a mat",
            "seed": 42,
        },
    )
    defaults.update(kw)
    return Artifact(**defaults)


def test_image_preview_contains_media_url():
    renderer = MediaPreviewRenderer()
    a = _make_image_artifact()
    html = renderer.image_preview(a)
    assert "https://example.com/img.png" in html
    assert "a cat on a mat" in html
    assert "replicate" in html


def test_image_preview_has_download_link():
    renderer = MediaPreviewRenderer()
    a = _make_image_artifact()
    html = renderer.image_preview(a)
    assert "تحميل" in html


def test_video_preview_contains_video_tag():
    renderer = MediaPreviewRenderer()
    a = _make_image_artifact(
        id="test-vid", type=ArtifactType.VIDEO,
        content={
            "media_url": "https://example.com/vid.mp4",
            "provider": "replicate",
            "model": "some-video-model",
            "prompt": "a running dog",
        },
    )
    html = renderer.video_preview(a)
    assert "https://example.com/vid.mp4" in html
    assert "<video" in html
