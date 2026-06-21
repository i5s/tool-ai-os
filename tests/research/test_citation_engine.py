from toll.research.citation_engine import CitationEngine
from toll.ports.research_source import ResearchSource, CitationStyle


def test_cite_apa_basic():
    engine = CitationEngine()
    source = ResearchSource(
        title="AI and the Future",
        authors=["Smith, J.", "Jones, A."],
        year=2024,
        journal="Journal of AI",
        volume="12",
        issue="3",
        pages="45-67",
        doi="10.1234/ai.2024.001",
        url="https://example.com",
        citation="Smith, J., & Jones, A. (2024). AI and the Future...",
        relevance_score=0.9,
        confidence_score=0.8,
        source_type="journal",
        provider="test",
    )
    result = engine.format(source, "apa")
    assert "Smith" in result
    assert "Jones" in result
    assert "2024" in result
    assert "AI and the Future" in result
    assert "Journal of AI" in result
    assert "12(3)" in result
    assert "45-67" in result
    assert "https://doi.org/10.1234/ai.2024.001" in result


def test_cite_apa_no_doi():
    engine = CitationEngine()
    source = ResearchSource(
        title="A Book",
        authors=["Smith, J."],
        year=2020,
        citation="Smith, J. (2020). A Book...",
        relevance_score=0.5,
        confidence_score=0.5,
        source_type="book",
        provider="test",
    )
    result = engine.format(source, "apa")
    assert "Smith" in result
    assert "A Book" in result


def test_cite_apa_no_author():
    engine = CitationEngine()
    source = ResearchSource(
        title="Untitled",
        year=2023,
        citation="Web source",
        relevance_score=0.3,
        confidence_score=0.3,
        source_type="web",
        provider="test",
    )
    result = engine.format(source, "apa")
    assert "Untitled" in result
    assert "2023" in result


def test_cite_mla():
    engine = CitationEngine()
    source = ResearchSource(
        title="MLA Example",
        authors=["Doe, John"],
        year=2021,
        journal="MLA Journal",
        volume="5",
        pages="10-20",
        doi="10.1234/mla.2021",
        citation="Doe. MLA Example...",
        relevance_score=0.8,
        confidence_score=0.7,
        source_type="journal",
        provider="test",
    )
    result = engine.format(source, "mla")
    assert "Doe" in result
    assert "MLA Example" in result
    assert "2021" in result
    assert "MLA Journal" in result


def test_cite_ieee():
    engine = CitationEngine()
    source = ResearchSource(
        title="IEEE Paper",
        authors=["Lee, K.", "Kim, S."],
        year=2022,
        pages="100-110",
        doi="10.1234/ieee.2022",
        citation="IEEE citation",
        relevance_score=0.8,
        confidence_score=0.8,
        source_type="conference",
        provider="test",
    )
    result = engine.format(source, "ieee")
    assert "K. Lee" in result
    assert "IEEE Paper" in result
    assert "2022" in result


def test_cite_chicago_notes():
    engine = CitationEngine()
    source = ResearchSource(
        title="Chicago Notes Book",
        authors=["Williams, M."],
        year=2019,
        publisher="UChicago Press",
        citation="Williams. Chicago Notes Book...",
        relevance_score=0.7,
        confidence_score=0.7,
        source_type="book",
        provider="test",
    )
    result = engine.format(source, "chicago_notes")
    assert "Williams" in result
    assert "Chicago Notes Book" in result
    assert "UChicago Press" in result


def test_cite_chicago_date():
    engine = CitationEngine()
    source = ResearchSource(
        title="Chicago Date Study",
        authors=["Adams, R."],
        year=2020,
        journal="Chicago Review",
        pages="30-40",
        doi="10.1234/chicago.2020",
        citation="Adams. Chicago Date Study...",
        relevance_score=0.7,
        confidence_score=0.7,
        source_type="journal",
        provider="test",
    )
    result = engine.format(source, "chicago_date")
    assert "Adams" in result
    assert "2020" in result
    assert "Chicago Date Study" in result


def test_cite_vancouver():
    engine = CitationEngine()
    source = ResearchSource(
        title="Vancouver Research",
        authors=["Patel, N.", "Gupta, R."],
        year=2023,
        journal="Vancouver Med J",
        volume="18",
        issue="2",
        pages="55-62",
        doi="10.1234/van.2023",
        citation="Patel. Vancouver Research...",
        relevance_score=0.8,
        confidence_score=0.8,
        source_type="journal",
        provider="test",
    )
    result = engine.format(source, "vancouver")
    assert "Patel" in result
    assert "Gupta" in result
    assert "Vancouver Research" in result
    assert "Vancouver Med J" in result


def test_format_batch_returns_list():
    engine = CitationEngine()
    sources = [
        ResearchSource(
            title=f"Source {i}",
            authors=[f"Author {i}"],
            year=2020 + i,
            citation=f"Source {i} citation",
            relevance_score=0.5,
            confidence_score=0.5,
            source_type="journal",
            provider="test",
        )
        for i in range(1, 4)
    ]
    results = engine.format_batch(sources, "apa")
    assert len(results) == 3
    assert all(isinstance(r, str) for r in results)


def test_export_bibtex_basic():
    engine = CitationEngine()
    sources = [
        ResearchSource(
            title="BibTeX Article",
            authors=["Miller, J.", "Davis, P."],
            year=2023,
            journal="BibTeX J",
            citation="Miller. BibTeX Article...",
            relevance_score=0.9,
            confidence_score=0.9,
            source_type="journal",
            provider="test",
        )
    ]
    result = engine.export_bibtex(sources)
    assert "@article" in result
    assert "BibTeX Article" in result
    assert "Miller" in result
    assert "Davis" in result


def test_export_bibtex_mixed_types():
    engine = CitationEngine()
    sources = [
        ResearchSource(
            title="Book Title",
            authors=["Smith, J."],
            year=2020,
            publisher="Press",
            citation="Book citation",
            relevance_score=0.8,
            confidence_score=0.8,
            source_type="book",
            provider="test",
        ),
        ResearchSource(
            title="Conf Paper",
            authors=["Lee, K."],
            year=2022,
            journal="Conf Proc",
            pages="50-60",
            citation="Conf citation",
            relevance_score=0.7,
            confidence_score=0.7,
            source_type="conference",
            provider="test",
        ),
    ]
    result = engine.export_bibtex(sources)
    assert "@book" in result
    assert "@inproceedings" in result


def test_export_ris():
    engine = CitationEngine()
    sources = [
        ResearchSource(
            title="RIS Article",
            authors=["Brown, T.", "Wilson, S."],
            year=2024,
            journal="RIS J",
            volume="3",
            pages="20-30",
            doi="10.1234/ris.2024",
            citation="Brown. RIS Article...",
            relevance_score=0.9,
            confidence_score=0.9,
            source_type="journal",
            provider="test",
        )
    ]
    result = engine.export_ris(sources)
    assert "TY  - JOUR" in result
    assert "TI  - RIS Article" in result
    assert "AU  - Brown, T." in result
    assert "AU  - Wilson, S." in result
    assert "DO  - 10.1234/ris.2024" in result


def test_unsupported_style_falls_back_to_apa():
    engine = CitationEngine()
    source = ResearchSource(
        title="Test",
        authors=["Author"],
        year=2024,
        citation="Test citation",
        relevance_score=0.5,
        confidence_score=0.5,
        source_type="web",
        provider="test",
    )
    result = engine.format(source, "nonexistent_style")
    assert result


def test_empty_sources_batch():
    engine = CitationEngine()
    assert engine.format_batch([], "apa") == []
    assert engine.export_bibtex([]) == ""
    assert engine.export_ris([]) == ""
