from toll.adapters.media.ollama import OllamaMediaAdapter
from toll.ports.media import MediaRequest


def test_not_available():
    adapter = OllamaMediaAdapter()
    assert adapter.is_available() is False


def test_no_supported_types():
    adapter = OllamaMediaAdapter()
    assert adapter.supported_types() == []


def test_generate_returns_error():
    adapter = OllamaMediaAdapter()
    result = adapter.generate(MediaRequest(prompt="test", media_type="image"))
    assert result.success is False
    assert "not yet supported" in result.error
