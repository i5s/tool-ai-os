import pytest
from toll.engine.renderers.carousel_renderer import CarouselRenderer
from toll.engine.renderers.report_renderer import ReportRenderer
from toll.engine.renderers.presentation_renderer import PresentationRenderer
from toll.engine.renderers.code_renderer import CodeRenderer
from toll.engine.renderers.preview_renderer import PreviewRenderer
from toll.model.artifact import Artifact, ArtifactType, ArtifactStatus


def test_carousel_renderer():
    r = CarouselRenderer()
    slides = [
        {"title": "S1", "subtitle": "Sub1", "content": "C1"},
        {"title": "S2", "subtitle": "Sub2", "content": "C2"},
    ]
    html = r.render("Test", slides)
    assert "S1" in html
    assert "S2" in html
    assert "carousel" in html.lower()


def test_report_renderer():
    r = ReportRenderer()
    sections = [
        {"heading": "Intro", "body": "Body text", "subsections": [
            {"subheading": "Sub", "body": "Sub body"},
        ]},
    ]
    html = r.render("Report Title", sections)
    assert "Report Title" in html
    assert "Intro" in html
    assert "Sub" in html


def test_presentation_renderer():
    r = PresentationRenderer()
    slides = [
        {"title": "Slide 1", "content": "Content 1"},
        {"title": "Slide 2", "content": "Content 2"},
    ]
    html = r.render("Pres Title", slides)
    assert "Slide 1" in html
    assert "Slide 2" in html
    assert "1/2" in html


def test_code_renderer():
    r = CodeRenderer()
    html = r.render("My Code", "print('hello')", "python")
    assert "My Code" in html
    assert "print" in html
    assert "python" in html.lower()


def test_preview_renderer_carousel():
    r = PreviewRenderer()
    art = Artifact(
        id="a1", type=ArtifactType.CAROUSEL, status=ArtifactStatus.COMPLETED, title="Carousel Preview",
        content={"slides": [{"title": "Slide 1", "content": "Content 1"}], "slide_count": 1},
        created_at="2026-01-01T00:00:00",
    )
    html = r.carousel_preview(art)
    assert "Carousel" in html
    assert "Slide 1" in html
    assert "index.html" in html


def test_preview_renderer_report():
    r = PreviewRenderer()
    art = Artifact(
        id="a1", type=ArtifactType.REPORT, status=ArtifactStatus.COMPLETED, title="Report Preview",
        content={"sections": [{"heading": "Intro", "body": "Hello"}]},
        created_at="2026-01-01T00:00:00",
    )
    html = r.report_preview(art)
    assert "Report" in html or "تقرير" in html
    assert "index.html" in html


def test_preview_renderer_presentation():
    r = PreviewRenderer()
    art = Artifact(
        id="a1", type=ArtifactType.PRESENTATION, status=ArtifactStatus.COMPLETED, title="Pres Preview",
        content={"slides": [{"title": "Slide 1", "content": "Content"}], "slide_count": 1},
        created_at="2026-01-01T00:00:00",
    )
    html = r.presentation_preview(art)
    assert "عرض" in html or "Presentation" in html
    assert "index.html" in html


def test_preview_renderer_json():
    r = PreviewRenderer()
    art = Artifact(
        id="a1", type=ArtifactType.REPORT, status=ArtifactStatus.COMPLETED, title="Json Preview",
        content={"sections": [{"heading": "Intro", "body": "Hello"}]},
        provider="opencode", intent="report", tags=["arabic"],
        created_at="2026-01-01T00:00:00",
    )
    data = r.json_preview(art)
    assert data["id"] == "a1"
    assert data["type"] == "report"
    assert data["provider"] == "opencode"
    assert data["intent"] == "report"
    assert data["tags"] == ["arabic"]
    assert "full_url" in data
    assert "preview_url" in data


def test_preview_renderer_generic():
    r = PreviewRenderer()
    art = Artifact(
        id="a1", type=ArtifactType.GENERIC, status=ArtifactStatus.COMPLETED, title="Generic",
        created_at="2026-01-01T00:00:00",
    )
    html = r.generic_preview(art)
    assert "Generic" in html
