from toll.adapters.media.replicate import ReplicateMediaAdapter
from toll.ports.media import MediaRequest


def test_is_not_available_without_package():
    adapter = ReplicateMediaAdapter()
    assert adapter.is_available() is False


def test_supported_types():
    adapter = ReplicateMediaAdapter()
    assert "image" in adapter.supported_types()
    assert len(adapter.supported_types()) == 1


def test_generate_returns_error_when_not_available():
    adapter = ReplicateMediaAdapter()
    result = adapter.generate(MediaRequest(prompt="test", media_type="image"))
    assert result.success is False
    assert "not installed" in result.error


def test_build_input_minimal():
    adapter = ReplicateMediaAdapter()
    params = adapter._build_input(MediaRequest(prompt="hello", media_type="image"))
    assert params["prompt"] == "hello"


def test_build_input_with_size():
    adapter = ReplicateMediaAdapter()
    params = adapter._build_input(MediaRequest(
        prompt="hello", media_type="image", size="1024x768",
    ))
    assert params["width"] == 1024
    assert params["height"] == 768


def test_build_input_with_seed():
    adapter = ReplicateMediaAdapter()
    params = adapter._build_input(MediaRequest(
        prompt="hello", media_type="image", seed=42,
    ))
    assert params["seed"] == 42


def test_build_input_with_negative_prompt():
    adapter = ReplicateMediaAdapter()
    params = adapter._build_input(MediaRequest(
        prompt="hello", media_type="image", negative_prompt="bad things",
    ))
    assert params["negative_prompt"] == "bad things"


def test_guess_content_type_png():
    adapter = ReplicateMediaAdapter()
    assert adapter._guess_content_type("https://example.com/image.png") == "image/png"


def test_guess_content_type_jpg():
    adapter = ReplicateMediaAdapter()
    assert adapter._guess_content_type("https://example.com/photo.jpg") == "image/jpeg"


def test_guess_content_type_webp():
    adapter = ReplicateMediaAdapter()
    assert adapter._guess_content_type("https://example.com/img.webp") == "image/webp"


def test_guess_content_type_unknown():
    adapter = ReplicateMediaAdapter()
    assert adapter._guess_content_type("https://example.com/file.bin") == "application/octet-stream"


def test_resolve_output_no_output():
    adapter = ReplicateMediaAdapter()
    url, data = adapter._resolve_output(None)
    assert url is None
    assert data is None


def test_resolve_output_string_url_returns_url_even_if_download_fails():
    adapter = ReplicateMediaAdapter()
    url, data = adapter._resolve_output("https://example.com/img.png")
    assert url == "https://example.com/img.png"
    assert data is None
