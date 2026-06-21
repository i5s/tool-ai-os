from toll.research.web_researcher import WebResearcher
from toll.ports.research_source import ResearchSource, ResearchQuery


def test_web_researcher_name():
    wr = WebResearcher()
    assert wr.name == "web"


def test_web_researcher_is_available():
    wr = WebResearcher()
    assert wr.is_available() is True


def test_cite():
    wr = WebResearcher()
    source = ResearchSource(
        title="Test",
        authors=["Author, A."],
        year=2024,
        citation="Test citation",
        relevance_score=0.5,
        confidence_score=0.5,
        source_type="web",
        provider="web",
    )
    result = wr.cite(source, "apa")
    assert isinstance(result, str)
    assert len(result) > 0


def test_synthesize():
    wr = WebResearcher()
    sources = [
        ResearchSource(
            title=f"Source {i}",
            citation=f"Snippet {i}",
            relevance_score=0.5,
            confidence_score=0.5,
            source_type="web",
            provider="web",
        )
        for i in range(3)
    ]
    result = wr.synthesize(sources, "Test Topic")
    assert "Test Topic" in result
    assert "Source 0" in result
