from toll.ports.media import MediaRequest, MediaResult


def test_media_request_defaults():
    req = MediaRequest(prompt="test", media_type="image", provider_model_id="m", provider="p")
    assert req.prompt == "test"
    assert req.media_type == "image"
    assert req.negative_prompt == ""
    assert req.seed is None
    assert req.metadata == {}


def test_media_request_all_fields():
    req = MediaRequest(
        prompt="test", media_type="video", provider_model_id="m", provider="p",
        negative_prompt="no", size="1920x1080", duration=10, seed=42,
        style="cinematic",
    )
    assert req.size == "1920x1080"
    assert req.duration == 10
    assert req.seed == 42


def test_media_result_success():
    result = MediaResult(
        success=True, media_path="images/uuid.png", media_type="image",
        provider="replicate", provider_model_id="flux-schnell",
        content_type="image/png", file_size_bytes=1024, width=512, height=512,
    )
    assert result.success
    assert result.media_path == "images/uuid.png"
    assert result.error is None


def test_media_result_error():
    result = MediaResult(success=False, error="Provider unavailable")
    assert not result.success
    assert result.error == "Provider unavailable"
    assert result.media_path is None
