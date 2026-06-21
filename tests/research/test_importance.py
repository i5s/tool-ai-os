from toll.research.importance import ImportanceScorer
from toll.ports.research_source import ResearchSource
from toll.memory.graph import Memory


def _make_source(
    relevance=0.0,
    confidence=0.0,
    citation_count=0,
):
    return ResearchSource(
        title="Test",
        relevance_score=relevance,
        confidence_score=confidence,
        citation_count=citation_count,
        source_type="web",
        provider="test",
    )


def test_compute_from_high_relevance():
    scorer = ImportanceScorer()
    source = _make_source(relevance=1.0, confidence=1.0, citation_count=200)
    score = scorer.compute(source)
    assert score == 10


def test_compute_from_mid_values():
    scorer = ImportanceScorer()
    source = _make_source(relevance=0.6, confidence=0.5, citation_count=50)
    score = scorer.compute(source)
    assert score == 5


def test_compute_from_low_values():
    scorer = ImportanceScorer()
    source = _make_source(relevance=0.1, confidence=0.1, citation_count=0)
    score = scorer.compute(source)
    assert score == 1


def test_compute_from_source_no_metadata():
    scorer = ImportanceScorer()
    source = _make_source()
    score = scorer.compute(source)
    assert score == 1


def test_compute_from_findings_with_sources():
    scorer = ImportanceScorer()
    score = scorer.compute_from_findings(["a", "b", "c"], 20)
    assert 1 <= score <= 10


def test_compute_from_findings_empty():
    scorer = ImportanceScorer()
    score = scorer.compute_from_findings([], 0)
    assert score == 1


def test_boost_on_retopic():
    scorer = ImportanceScorer()
    result = scorer.boost_on_retopic(5, 2)
    assert result == 7


def test_boost_on_retopic_capped():
    scorer = ImportanceScorer()
    result = scorer.boost_on_retopic(8, 5)
    assert result == 10


def test_decay_within_window():
    scorer = ImportanceScorer()
    result = scorer.decay(5, 30, max_days=90, delta=-1)
    assert result == 5


def test_decay_beyond_window():
    scorer = ImportanceScorer()
    result = scorer.decay(5, 100, max_days=90, delta=-1)
    assert result == 4


def test_decay_floor():
    scorer = ImportanceScorer()
    result = scorer.decay(1, 100, max_days=90, delta=-1)
    assert result == 1


def test_should_include_above_threshold():
    scorer = ImportanceScorer()
    mem = Memory(
        id="m1", type="knowledge", entity_id=None, key="k", value="v",
        importance_score=5, source="test",
        created_at="", updated_at="", last_accessed_at="",
    )
    assert scorer.should_include_in_context(mem) is True


def test_should_include_below_threshold():
    scorer = ImportanceScorer()
    mem = Memory(
        id="m2", type="knowledge", entity_id=None, key="k", value="v",
        importance_score=3, source="test",
        created_at="", updated_at="", last_accessed_at="",
    )
    assert scorer.should_include_in_context(mem) is False


def test_should_include_custom_threshold():
    scorer = ImportanceScorer()
    mem = Memory(
        id="m3", type="knowledge", entity_id=None, key="k", value="v",
        importance_score=3, source="test",
        created_at="", updated_at="", last_accessed_at="",
    )
    assert scorer.should_include_in_context(mem, threshold=3) is True
