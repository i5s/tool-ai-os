import os
from toll.core.settings import Settings, DEFAULTS


def test_settings_defaults(storage):
    settings = Settings(storage=storage)
    assert settings.get("ollama_model") == DEFAULTS["ollama_model"]
    assert settings.get("daily_limit_opencode") == "20"


def test_settings_env_override(storage, monkeypatch):
    monkeypatch.setenv("TOLL_OLLAMA_MODEL", "llama3")
    settings = Settings(storage=storage)
    assert settings.get("ollama_model") == "llama3"


def test_settings_db_override(storage):
    storage.set_config("ollama_model", "mistral")
    settings = Settings(storage=storage)
    assert settings.get("ollama_model") == "mistral"


def test_settings_env_beats_db(storage, monkeypatch):
    storage.set_config("ollama_model", "mistral")
    monkeypatch.setenv("TOLL_OLLAMA_MODEL", "llama3")
    settings = Settings(storage=storage)
    assert settings.get("ollama_model") == "llama3"
