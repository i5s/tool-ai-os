from toll.benchmark.quality_scorer import QualityScorer


def test_score_empty_registry():
    scorer = QualityScorer()
    assert scorer.score({}) == 0.0


def test_latency_below_1s():
    scorer = QualityScorer()
    scorer.register_criterion("latency_ms")
    assert scorer.score({"provider_latency_ms": 500}) == 1.0


def test_latency_between_1_and_5s():
    scorer = QualityScorer()
    scorer.register_criterion("latency_ms")
    assert scorer.score({"provider_latency_ms": 3000}) == 0.7


def test_latency_over_15s():
    scorer = QualityScorer()
    scorer.register_criterion("latency_ms")
    assert scorer.score({"provider_latency_ms": 20000}) == 0.1


def test_no_error_true():
    scorer = QualityScorer()
    scorer.register_criterion("no_error")
    assert scorer.score({"error": None}) == 1.0


def test_no_error_false():
    scorer = QualityScorer()
    scorer.register_criterion("no_error")
    assert scorer.score({"error": "something broke"}) == 0.0


def test_weighted_score():
    scorer = QualityScorer()
    scorer.register_criterion("no_error", weight=2.0)
    scorer.register_criterion("latency_ms", weight=1.0)
    score = scorer.score({
        "error": None,
        "provider_latency_ms": 3000,
    })
    weight_sum = 2.0 + 1.0
    expected = (1.0 * 2.0 + 0.7 * 1.0) / weight_sum
    assert score == round(expected, 2)


def test_unknown_criterion_returns_none():
    scorer = QualityScorer()
    scorer.register_criterion("unknown")
    assert scorer.score({"some": "data"}) == 0.0


def test_file_size_above_50k():
    scorer = QualityScorer()
    scorer.register_criterion("file_size_bytes")
    assert scorer.score({"file_size_bytes": 100000}) == 1.0


def test_file_size_between_10k_and_50k():
    scorer = QualityScorer()
    scorer.register_criterion("file_size_bytes")
    assert scorer.score({"file_size_bytes": 20000}) == 0.7


def test_file_size_below_10k():
    scorer = QualityScorer()
    scorer.register_criterion("file_size_bytes")
    assert scorer.score({"file_size_bytes": 5000}) == 0.4
