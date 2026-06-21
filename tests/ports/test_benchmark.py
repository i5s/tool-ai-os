from toll.ports.benchmark import BenchmarkRun, BenchmarkSuite


def test_benchmark_run_defaults():
    run = BenchmarkRun(id="r1", model_id="m1", prompt="test", media_type="image")
    assert run.quality_score_auto == 0.0
    assert run.error is None
    assert run.suite_id is None


def test_benchmark_run_with_error():
    run = BenchmarkRun(id="r1", model_id="m1", prompt="test", media_type="image",
                       error="Timeout")
    assert run.error == "Timeout"


def test_benchmark_suite_defaults():
    suite = BenchmarkSuite(id="s1", name="Test")
    assert suite.prompts == []
    assert suite.media_type == "image"


def test_benchmark_suite_with_prompts():
    suite = BenchmarkSuite(id="s1", name="Test", prompts=["p1", "p2"], media_type="video")
    assert len(suite.prompts) == 2
