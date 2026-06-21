import pytest
from pathlib import Path
from toll.application.research_service import ResearchService
from toll.application.artifact_service import ArtifactService
from toll.core.provider_selector import ProviderSelector
from toll.core.registry import ProviderRegistry
from toll.core.settings import Settings
from toll.core.feature_flags import FeatureFlags
from toll.ports.research_source import CitationStyle


@pytest.fixture
def research_service(cm, tmp_path):
    import toll.core.config as cfg
    cfg.ARTIFACTS_PATH = tmp_path / "artifacts"
    cfg.ARCHIVE_PATH = cfg.ARTIFACTS_PATH / "archive"

    settings = Settings(cm=cm)
    registry = ProviderRegistry(settings)
    flags = FeatureFlags(cm=cm)
    flags.enable("research_provider")
    selector = ProviderSelector(registry, settings, flags)
    artifact_service = ArtifactService(cm)
    return ResearchService(artifact_service, selector, cm, flags)


def test_execute_quick(research_service):
    plan = {"title": "بحث سريع", "max_sources": 3}
    result = research_service.execute_quick(plan)
    assert result["type"] == "research_quick"
    assert result["title"] == "بحث سريع"
    assert "source_count" in result


def test_execute_creates_artifact(research_service):
    plan = {"title": "اختبار البحث", "max_sources": 3, "style": "apa"}
    result = research_service.execute(plan)
    assert result["type"] == "research"
    assert result["artifact_id"] != ""
    assert result["source_count"] >= 0


def test_fallback_synthesis(research_service):
    result = research_service._fallback_synthesis("موضوع اختبار")
    assert "موضوع اختبار" in result


def test_extract_findings(research_service):
    synopsis = "هذه هي النتيجة الأولى. هذه هي النتيجة الثانية. هذه هي النتيجة الثالثة."
    findings = research_service._extract_findings(synopsis)
    assert len(findings) == 3
    assert all(len(f) > 20 for f in findings)


def test_citation_styles_enum():
    assert CitationStyle.APA.value == "apa"
    assert CitationStyle.MLA.value == "mla"
    assert CitationStyle.IEEE.value == "ieee"
    assert CitationStyle.CHICAGO_NOTES.value == "chicago_notes"
    assert CitationStyle.CHICAGO_DATE.value == "chicago_date"
    assert CitationStyle.VANCOUVER.value == "vancouver"
