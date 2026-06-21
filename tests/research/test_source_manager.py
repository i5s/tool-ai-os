from toll.research.source_manager import SourceManager
from toll.research.citation_engine import CitationEngine
from toll.ports.research_source import ResearchSource, ResearchQuery


def _ensure_artifact(cm, artifact_id="art_001"):
    cm.execute(
        "INSERT OR IGNORE INTO artifacts (id, type, status, title, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (artifact_id, "research", "draft", "Test Artifact", "{}", "2026-01-01", "2026-01-01"),
    )
    cm.commit()


def test_collect_with_no_providers():
    manager = SourceManager()
    query = ResearchQuery(query="test topic")
    sources = manager.collect(query, [])
    assert sources == []


def test_store_and_get(cm):
    _ensure_artifact(cm, "art_001")
    manager = SourceManager(cm=cm)
    source = ResearchSource(
        title="Stored Article",
        authors=["Test, A."],
        year=2024,
        citation="Stored article citation",
        relevance_score=0.85,
        confidence_score=0.75,
        source_type="journal",
        provider="test_provider",
    )
    result = manager.store(source, "art_001")
    assert result.title == "Stored Article"

    stored = manager.list("art_001")
    assert len(stored) >= 1
    assert stored[0].title == "Stored Article"


def test_get_source(cm):
    _ensure_artifact(cm, "art_get")
    manager = SourceManager(cm=cm)
    source = ResearchSource(
        title="Get Me",
        citation="Get me citation",
        relevance_score=0.5,
        confidence_score=0.5,
        source_type="web",
        provider="test",
    )
    manager.store(source, "art_get")

    sources = manager.list("art_get")
    assert len(sources) >= 1
    sid = sources[0].id
    retrieved = manager.get(sid)
    assert retrieved is not None
    assert retrieved.title == "Get Me"


def test_delete_source(cm):
    _ensure_artifact(cm, "art_del")
    manager = SourceManager(cm=cm)
    source = ResearchSource(
        title="Delete Me",
        citation="Delete me",
        relevance_score=0.5,
        confidence_score=0.5,
        source_type="web",
        provider="test",
    )
    manager.store(source, "art_del")
    sources = manager.list("art_del")
    assert len(sources) >= 1
    sid = sources[0].id
    result = manager.delete_source(sid)
    assert result is True
    deleted = manager.get(sid)
    assert deleted is None


def test_add_tags_to_source(cm):
    _ensure_artifact(cm, "art_tags")
    manager = SourceManager(cm=cm)
    source = ResearchSource(
        title="Tag Me",
        citation="Tag me",
        relevance_score=0.5,
        confidence_score=0.5,
        source_type="web",
        provider="test",
    )
    manager.store(source, "art_tags")
    sources = manager.list("art_tags")
    assert len(sources) >= 1
    sid = sources[0].id
    result = manager.add_tags(sid, ["tag1", "tag2"])
    assert result is None


def test_import_bibtex():
    manager = SourceManager()
    bibtex_str = """@article{test2024,
  title = {Imported Article},
  author = {Smith, John and Doe, Jane},
  year = {2024},
  journal = {Test Journal},
  doi = {10.1234/test.2024}
}"""
    result = manager.import_bibtex(bibtex_str)
    assert len(result) > 0
    assert result[0].title == "Imported Article"


def test_import_ris():
    manager = SourceManager()
    ris_str = """TY  - JOUR
TI  - Imported RIS Article
AU  - Wilson, Tom
PY  - 2024
DO  - 10.1234/ris.import
ER  - """
    result = manager.import_ris(ris_str)
    assert len(result) > 0
    assert result[0].title == "Imported RIS Article"


def test_ranking_respects_weighting():
    manager = SourceManager()
    sources = [
        ResearchSource(
            title="High relevance, low confidence",
            relevance_score=0.9,
            confidence_score=0.2,
            citation="A",
            source_type="web",
            provider="test",
        ),
        ResearchSource(
            title="Medium both",
            relevance_score=0.5,
            confidence_score=0.5,
            citation="B",
            source_type="web",
            provider="test",
        ),
    ]
    manager._rank(sources)
    assert sources[0].title == "High relevance, low confidence"
