from toll.prompt.memory import PromptMemory
from toll.prompt.repository import PromptProfile, PromptProfileRepository


def _ensure_profile(cm, profile_id="p1"):
    repo = PromptProfileRepository(cm)
    existing = repo.get(profile_id)
    if not existing:
        repo.create(PromptProfile(id=profile_id, name="Test Profile"))


def test_record_success(cm):
    _ensure_profile(cm)
    mem = PromptMemory(cm)
    mem.record_success(profile_id="p1", model_id="r:flux",
                       prompt="a cat", artifact_id="art:123", score=0.85)
    avg = mem.get_avg_score("p1")
    assert avg == 0.85


def test_record_multiple_scores(cm):
    _ensure_profile(cm)
    mem = PromptMemory(cm)
    mem.record_success("p1", "m1", "prompt1", score=0.9)
    mem.record_success("p1", "m1", "prompt2", score=0.7)
    avg = mem.get_avg_score("p1")
    assert avg == 0.8


def test_get_avg_score_no_data(cm):
    mem = PromptMemory(cm)
    assert mem.get_avg_score("nonexistent") is None


def test_get_avg_score_per_model(cm):
    _ensure_profile(cm)
    _ensure_profile(cm, "p2")
    repo = PromptProfileRepository(cm)
    repo.create(PromptProfile(id="p2", name="P2"))
    mem = PromptMemory(cm)
    mem.record_success("p1", "m1", "p", score=0.9)
    mem.record_success("p1", "m2", "p", score=0.5)
    avg = mem.get_avg_score("p1", model_id="m1")
    assert avg == 0.9


def test_blacklist_and_check(cm):
    _ensure_profile(cm)
    mem = PromptMemory(cm)
    assert mem.is_blacklisted("p1", "m1") is False
    mem.record_failure("p1", "m1", "repeated errors")
    assert mem.is_blacklisted("p1", "m1") is True


def test_blacklist_unique_constraint(cm):
    _ensure_profile(cm)
    mem = PromptMemory(cm)
    mem.record_failure("p1", "m1", "error 1")
    mem.record_failure("p1", "m1", "error 2")
    assert mem.is_blacklisted("p1", "m1") is True


def test_get_consecutive_failures(cm):
    _ensure_profile(cm)
    mem = PromptMemory(cm)
    assert mem.get_consecutive_failures("p1", "m1") == 0
    mem.record_success("p1", "m1", "ok", score=None)
    mem.record_success("p1", "m1", "fail", score=None)
    count = mem.get_consecutive_failures("p1", "m1")
    assert count >= 2
