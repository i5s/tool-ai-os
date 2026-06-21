from toll.benchmark.service import BenchmarkService
from toll.core.registry import ProviderRegistry


def _make_svc(cm, feature_flags):
    registry = ProviderRegistry()
    return BenchmarkService(cm=cm, registry=registry, flags=feature_flags)


def test_create_suite_missing_name(cm, feature_flags):
    svc = _make_svc(cm, feature_flags)
    result = svc.create_suite({"name": ""})
    assert result["success"] is False
    assert "name" in result["error"]


def test_create_suite_no_prompts(cm, feature_flags):
    svc = _make_svc(cm, feature_flags)
    result = svc.create_suite({"name": "Test", "prompts": []})
    assert result["success"] is False
    assert "prompt" in result["error"]


def test_create_suite_success(cm, feature_flags):
    svc = _make_svc(cm, feature_flags)
    result = svc.create_suite({
        "name": "Benchmark 1",
        "prompts": ["a cat", "a dog"],
        "media_type": "image",
    })
    assert result["success"] is True
    assert result["name"] == "Benchmark 1"
    assert result["prompts"] == 2


def test_list_suites_empty(cm, feature_flags):
    svc = _make_svc(cm, feature_flags)
    result = svc.list_suites()
    assert result["success"] is True
    assert result["suites"] == []


def test_list_suites_with_data(cm, feature_flags):
    svc = _make_svc(cm, feature_flags)
    svc.create_suite({"name": "S1", "prompts": ["p1"], "media_type": "image"})
    result = svc.list_suites()
    assert len(result["suites"]) == 1


def test_get_suite_not_found(cm, feature_flags):
    svc = _make_svc(cm, feature_flags)
    result = svc.get_suite("nonexistent")
    assert result["success"] is False


def test_model_scores_empty(cm, feature_flags):
    svc = _make_svc(cm, feature_flags)
    result = svc.model_scores("r:test")
    assert result["success"] is True
    assert result["run_count"] == 0


def test_list_runs_empty(cm, feature_flags):
    svc = _make_svc(cm, feature_flags)
    result = svc.list_runs()
    assert result["success"] is True
    assert result["runs"] == []


def test_execute_missing_params(cm, feature_flags):
    svc = _make_svc(cm, feature_flags)
    result = svc.execute({})
    assert result["success"] is False
