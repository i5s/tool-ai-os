from toll.core.provider_selector import ProviderSelector
from toll.core.registry import ProviderRegistry
from toll.core.settings import Settings


class FakeBenchmarkRepo:
    def __init__(self, scores=None):
        self._scores = scores or {}

    def avg_scores(self, model_id):
        return self._scores.get(model_id, {})


def test_benchmark_aware_quality_uses_benchmark_when_enabled(feature_flags):
    feature_flags.enable("benchmark_auto_quality")
    repo = FakeBenchmarkRepo({"opencode": {"avg_quality_auto": 0.75}})
    selector = ProviderSelector(ProviderRegistry(), Settings(), feature_flags,
                                benchmark_repo=repo)
    score = selector._quality_score("opencode")
    assert score == 0.75


def test_benchmark_aware_falls_back_to_static_when_no_data(feature_flags):
    feature_flags.enable("benchmark_auto_quality")
    repo = FakeBenchmarkRepo({})
    selector = ProviderSelector(ProviderRegistry(), Settings(), feature_flags,
                                benchmark_repo=repo)
    score = selector._quality_score("opencode")
    assert score == 0.9


def test_benchmark_aware_ignored_when_flag_disabled(feature_flags):
    repo = FakeBenchmarkRepo({"opencode": {"avg_quality_auto": 0.75}})
    selector = ProviderSelector(ProviderRegistry(), Settings(), feature_flags,
                                benchmark_repo=repo)
    score = selector._quality_score("opencode")
    assert score == 0.9


def test_benchmark_aware_unknown_provider_falls_to_static(feature_flags):
    feature_flags.enable("benchmark_auto_quality")
    repo = FakeBenchmarkRepo({})
    selector = ProviderSelector(ProviderRegistry(), Settings(), feature_flags,
                                benchmark_repo=repo)
    score = selector._quality_score("unknown")
    assert score == 0.3
