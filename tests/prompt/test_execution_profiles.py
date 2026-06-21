from toll.prompt.execution_profile import ExecutionProfileRepository


def test_list_default_profiles():
    repo = ExecutionProfileRepository()
    profiles = repo.list()
    assert len(profiles) == 6
    ids = {p.id for p in profiles}
    assert "research" in ids
    assert "marketing" in ids
    assert "presentation" in ids


def test_get_profile():
    repo = ExecutionProfileRepository()
    p = repo.get("marketing")
    assert p is not None
    assert p.name == "Marketing Profile"
    assert "product_ad" in p.sub_profiles


def test_get_missing_profile():
    repo = ExecutionProfileRepository()
    assert repo.get("nonexistent") is None


def test_resolve_prompt_profile_direct_match():
    repo = ExecutionProfileRepository()
    result = repo.resolve_prompt_profile("marketing", "product_ad")
    assert result == "product_ad"


def test_resolve_prompt_profile_first_fallback():
    repo = ExecutionProfileRepository()
    result = repo.resolve_prompt_profile("marketing", "unknown_intent")
    assert result == "product_ad"


def test_resolve_empty_sub_profiles():
    repo = ExecutionProfileRepository()
    result = repo.resolve_prompt_profile("nonexistent", "test")
    assert result is None
