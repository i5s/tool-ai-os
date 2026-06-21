from toll.benchmark.runner import BenchmarkRunner
from toll.benchmark.repository import BenchmarkRepository
from toll.core.registry import ProviderRegistry
from toll.ports.media import MediaPort, MediaRequest, MediaResult


class FakeBenchmarkAdapter(MediaPort):
    name = "fake"

    def generate(self, request: MediaRequest) -> MediaResult:
        return MediaResult(
            success=True,
            url="https://example.com/img.png",
            media_data=b"img",
            media_type="image",
            content_type="image/png",
            file_size_bytes=51200,
        )


def _ensure_model(cm, model_id="r:test"):
    parts = model_id.split(":", 1)
    provider_model = parts[1] if len(parts) > 1 else "test"
    cm.execute(
        "INSERT OR IGNORE INTO models (id, provider, provider_model_id, name) VALUES (?, ?, ?, ?)",
        (model_id, "replicate", provider_model, "Test Model"),
    )
    cm.commit()


def test_run_prompt_success(cm):
    _ensure_model(cm)
    repo = BenchmarkRepository(cm)
    registry = ProviderRegistry()
    registry.register_media("fake", FakeBenchmarkAdapter())
    runner = BenchmarkRunner(repo, registry)
    result = runner.run_prompt("r:test", "a cat", media_type="image")
    assert result["success"] is True
    assert result["quality_score"] > 0


def test_run_prompt_records_run(cm):
    _ensure_model(cm)
    repo = BenchmarkRepository(cm)
    registry = ProviderRegistry()
    registry.register_media("fake", FakeBenchmarkAdapter())
    runner = BenchmarkRunner(repo, registry)
    result = runner.run_prompt("r:test", "a cat", media_type="image")
    runs = repo.list_runs(model_id="r:test")
    assert len(runs) == 1


def test_run_suite_with_fake_adapter(cm):
    _ensure_model(cm)
    repo = BenchmarkRepository(cm)
    registry = ProviderRegistry()
    registry.register_media("fake", FakeBenchmarkAdapter())
    runner = BenchmarkRunner(repo, registry)
    suite = repo.create_suite("Test Suite", ["cat", "dog"], "image")
    result = runner.run_suite(suite.id, "r:test")
    assert result["success"] is True
    assert result["prompts_completed"] == 2


def test_run_suite_not_found(cm):
    repo = BenchmarkRepository(cm)
    registry = ProviderRegistry()
    runner = BenchmarkRunner(repo, registry)
    result = runner.run_suite("nonexistent", "r:test")
    assert result["success"] is False
    assert "not found" in result["error"]
