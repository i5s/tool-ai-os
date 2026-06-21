from toll.benchmark.repository import BenchmarkRepository


def _ensure_model(cm, model_id="r:test"):
    parts = model_id.split(":", 1)
    provider_model = parts[1] if len(parts) > 1 else "test"
    cm.execute(
        "INSERT OR IGNORE INTO models (id, provider, provider_model_id, name) VALUES (?, ?, ?, ?)",
        (model_id, "replicate", provider_model, "Test Model"),
    )
    cm.commit()


def test_create_and_get_suite(cm):
    repo = BenchmarkRepository(cm)
    suite = repo.create_suite(
        name="Test Suite",
        prompts=["a cat", "a dog"],
        media_type="image",
        description="test",
    )
    got = repo.get_suite(suite.id)
    assert got is not None
    assert got.name == "Test Suite"
    assert len(got.prompts) == 2


def test_list_suites(cm):
    repo = BenchmarkRepository(cm)
    repo.create_suite(name="S1", prompts=["p1"], media_type="image")
    repo.create_suite(name="S2", prompts=["p2"], media_type="image")
    suites = repo.list_suites()
    assert len(suites) >= 2


def test_delete_suite_removes_runs(cm):
    _ensure_model(cm)
    repo = BenchmarkRepository(cm)
    suite = repo.create_suite(name="Del", prompts=["p"], media_type="image")
    run = repo.create_run(model_id="r:test", prompt="p", media_type="image", suite_id=suite.id)
    repo.delete_suite(suite.id)
    assert repo.get_suite(suite.id) is None
    assert repo.get_run(run.id) is None


def test_create_and_get_run(cm):
    _ensure_model(cm)
    repo = BenchmarkRepository(cm)
    run = repo.create_run(model_id="r:test", prompt="a cat", media_type="image")
    got = repo.get_run(run.id)
    assert got is not None
    assert got.model_id == "r:test"
    assert got.prompt == "a cat"


def test_update_run(cm):
    _ensure_model(cm)
    repo = BenchmarkRepository(cm)
    run = repo.create_run(model_id="r:test", prompt="p", media_type="image")
    repo.update_run(run.id, quality_score_auto=0.85, error=None)
    updated = repo.get_run(run.id)
    assert updated.quality_score_auto == 0.85


def test_list_runs_filter_by_model(cm):
    _ensure_model(cm, "r:a")
    _ensure_model(cm, "r:b")
    repo = BenchmarkRepository(cm)
    repo.create_run(model_id="r:a", prompt="p1", media_type="image")
    repo.create_run(model_id="r:b", prompt="p2", media_type="image")
    runs = repo.list_runs(model_id="r:a")
    assert len(runs) == 1
    assert runs[0].model_id == "r:a"


def test_avg_scores_empty(cm):
    repo = BenchmarkRepository(cm)
    scores = repo.avg_scores("nonexistent")
    assert scores["run_count"] == 0
    assert scores["avg_quality_auto"] is None


def test_avg_scores_with_data(cm):
    _ensure_model(cm)
    repo = BenchmarkRepository(cm)
    r1 = repo.create_run(model_id="r:test", prompt="p1", media_type="image")
    r2 = repo.create_run(model_id="r:test", prompt="p2", media_type="image")
    repo.update_run(r1.id, quality_score_auto=0.8, provider_latency_ms=500, file_size_bytes=1000)
    repo.update_run(r2.id, quality_score_auto=0.6, provider_latency_ms=1500, file_size_bytes=2000)
    scores = repo.avg_scores("r:test")
    assert scores["avg_quality_auto"] == 0.7
    assert scores["run_count"] == 2
