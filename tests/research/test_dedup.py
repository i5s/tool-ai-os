from toll.research.dedup import DedupEngine
from toll.ports.research_source import ResearchSource


def test_no_duplicates_returns_all():
    engine = DedupEngine()
    sources = [
        ResearchSource(
            title="A", url="http://a.com", doi="10.1/a",
            citation="A", relevance_score=0.5, confidence_score=0.5,
            source_type="journal", provider="test",
        ),
        ResearchSource(
            title="B", url="http://b.com", doi="10.1/b",
            citation="B", relevance_score=0.5, confidence_score=0.5,
            source_type="journal", provider="test",
        ),
    ]
    deduped = engine.dedup(sources)
    assert len(deduped) == 2


def test_doi_duplicate_removes_one():
    engine = DedupEngine()
    sources = [
        ResearchSource(
            title="Original", doi="10.1/dup",
            citation="Original", relevance_score=0.9, confidence_score=0.8,
            source_type="journal", provider="test",
        ),
        ResearchSource(
            title="Duplicate", doi="10.1/dup",
            citation="Duplicate", relevance_score=0.8, confidence_score=0.7,
            source_type="journal", provider="test",
        ),
    ]
    deduped = engine.dedup(sources)
    assert len(deduped) == 1
    assert deduped[0].title == "Original"


def test_url_duplicate_removes_one():
    engine = DedupEngine()
    sources = [
        ResearchSource(
            title="First", url="http://same.url/article",
            citation="First", relevance_score=0.9, confidence_score=0.8,
            source_type="web", provider="test",
        ),
        ResearchSource(
            title="Second", url="http://same.url/article",
            citation="Second", relevance_score=0.8, confidence_score=0.7,
            source_type="web", provider="test",
        ),
    ]
    deduped = engine.dedup(sources)
    assert len(deduped) == 1
    assert deduped[0].title == "First"


def test_title_similarity_removes_duplicate():
    engine = DedupEngine()
    sources = [
        ResearchSource(
            title="The Impact of AI on Modern Healthcare",
            citation="citation1", relevance_score=0.9, confidence_score=0.8,
            source_type="journal", provider="test",
        ),
        ResearchSource(
            title="The Impact of AI on Modern Healthcare",
            citation="citation2", relevance_score=0.8, confidence_score=0.7,
            source_type="journal", provider="test",
        ),
    ]
    deduped = engine.dedup(sources)
    assert len(deduped) == 1


def test_title_similarity_keeps_different():
    engine = DedupEngine()
    sources = [
        ResearchSource(
            title="AI in Healthcare", citation="A",
            relevance_score=0.5, confidence_score=0.5,
            source_type="journal", provider="test",
        ),
        ResearchSource(
            title="Climate Change Effects", citation="B",
            relevance_score=0.5, confidence_score=0.5,
            source_type="journal", provider="test",
        ),
    ]
    deduped = engine.dedup(sources)
    assert len(deduped) == 2


def test_author_year_composite():
    engine = DedupEngine()
    sources = [
        ResearchSource(
            title="Paper One", authors=["Smith, J.", "Jones, A."], year=2024,
            citation="Paper One", relevance_score=0.9, confidence_score=0.8,
            source_type="journal", provider="test",
        ),
        ResearchSource(
            title="Paper One (similar)", authors=["Smith, J.", "Jones, A."], year=2024,
            citation="Paper One similar", relevance_score=0.8, confidence_score=0.7,
            source_type="journal", provider="test",
        ),
    ]
    deduped = engine.dedup(sources)
    assert len(deduped) == 1


def test_empty_sources():
    engine = DedupEngine()
    assert engine.dedup([]) == []


def test_single_source():
    engine = DedupEngine()
    sources = [
        ResearchSource(
            title="Only One", citation="Only",
            relevance_score=0.5, confidence_score=0.5,
            source_type="journal", provider="test",
        ),
    ]
    deduped = engine.dedup(sources)
    assert len(deduped) == 1


def test_dedup_logs_to_db(cm):
    engine = DedupEngine(cm=cm)
    sources = [
        ResearchSource(
            title="Log Test A", doi="10.2/log",
            citation="A", relevance_score=0.5, confidence_score=0.5,
            source_type="journal", provider="test",
        ),
        ResearchSource(
            title="Log Test B", doi="10.2/log",
            citation="B", relevance_score=0.5, confidence_score=0.5,
            source_type="journal", provider="test",
        ),
    ]
    deduped = engine.dedup(sources)
    assert len(deduped) == 1
    rows = cm.connection.execute("SELECT * FROM research_dedup_log").fetchall()
    assert len(rows) >= 1
    assert rows[0]["strategy"] == "doi"
