import pytest
from toll.core.feature_flags import FeatureFlags, DEFAULT_FLAGS


def test_core_flags_enabled_by_default(feature_flags: FeatureFlags):
    core_flags = [
        "core_chat",
        "planner_enabled",
        "workflow_enabled",
        "memory_graph",
        "workspace_manager",
        "context_engine",
    ]
    for flag in core_flags:
        assert feature_flags.is_enabled(flag) is True, f"{flag} should be enabled"


def test_dormant_flags_disabled_by_default(feature_flags: FeatureFlags):
    dormant_flags = [
        "telegram_enabled",
        "knowledge_vault",
        "preference_memory",
        "google_drive_sync",
    ]
    for flag in dormant_flags:
        assert feature_flags.is_enabled(flag) is False, f"{flag} should be disabled"


def test_enable_disable(feature_flags: FeatureFlags):
    feature_flags.disable("core_chat")
    assert feature_flags.is_enabled("core_chat") is False

    feature_flags.enable("core_chat")
    assert feature_flags.is_enabled("core_chat") is True

    feature_flags.set("core_chat", False)
    assert feature_flags.is_enabled("core_chat") is False


def test_get_all_returns_known_flags(feature_flags: FeatureFlags):
    all_flags = feature_flags.get_all()
    assert set(all_flags.keys()) == set(DEFAULT_FLAGS.keys())
    for name, default in DEFAULT_FLAGS.items():
        assert all_flags[name] == default


def test_unknown_flag_uses_default(feature_flags: FeatureFlags):
    assert feature_flags.is_enabled("nonexistent_flag", default=True) is True
    assert feature_flags.is_enabled("nonexistent_flag", default=False) is False
