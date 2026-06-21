from __future__ import annotations

import logging

from ..core.ai import AI
from ..core.connection_manager import ConnectionManager
from ..core.provider_selector import ProviderSelector
from ..engine.renderers.preview_renderer import PreviewRenderer
from ..engine.renderers.presentation_renderer import PresentationRenderer
from ..model.artifact import Artifact, ArtifactStatus, ArtifactType
from .artifact_service import ArtifactService

logger = logging.getLogger(__name__)


class PresentationService:
    def __init__(self, artifact_service: ArtifactService, selector: ProviderSelector, cm: ConnectionManager):
        self.artifact_service = artifact_service
        self.selector = selector
        self.cm = cm
        self.ai = AI(cm=cm)
        self.renderer = PresentationRenderer()
        self.preview = PreviewRenderer()

    def execute(self, plan: dict, metadata: dict | None = None) -> dict:
        title = plan.get("title", plan.get("intent", "presentation"))
        slide_count = plan.get("slides", 5)
        style = plan.get("style", "editorial")

        provider_name = self.selector.select(ArtifactType.PRESENTATION)
        if not provider_name:
            return {"error": "No available provider for presentation generation"}

        prompt = self._build_prompt(title, slide_count, style)
        try:
            raw = self.ai.ask(prompt)
        except RuntimeError as e:
            return {"error": str(e)}

        slides = self._parse_slides(raw) or self._fallback_slides(title, slide_count)

        artifact = Artifact(
            id="",
            type=ArtifactType.PRESENTATION,
            status=ArtifactStatus.DRAFT,
            title=title,
            content={"slides": slides, "style": style, "slide_count": slide_count},
            provider=provider_name,
            intent="presentation",
            workflow_id=metadata.get("workflow_id") if metadata else None,
            conversation_id=metadata.get("conversation_id") if metadata else None,
        )

        rendered = self.renderer.render(title, slides)
        artifact = self.artifact_service.create(artifact, rendered)

        preview_html = self.preview.presentation_preview(artifact)
        preview_json = self.preview.json_preview(artifact)
        self.artifact_service.write_preview(artifact, preview_html, preview_json)

        return {
            "artifact_id": artifact.id,
            "type": "presentation",
            "title": title,
            "slides": len(slides),
            "preview_url": artifact.preview_url,
            "rendered_path": artifact.rendered_path,
        }

    def _build_prompt(self, title: str, count: int, style: str) -> str:
        return (
            f"Write {count} slides for a presentation titled '{title}' in Arabic.\n"
            f"Style: {style}.\n"
            f"Return each slide as exactly:\n"
            f"SLIDE | Title | Content\n"
        )

    def _parse_slides(self, raw: str) -> list[dict] | None:
        slides = []
        for line in raw.strip().split("\n"):
            line = line.strip()
            if line.startswith("SLIDE |"):
                parts = line.split("|")
                if len(parts) >= 3:
                    slides.append({
                        "title": parts[1].strip(),
                        "content": "|".join(parts[2:]).strip(),
                    })
        return slides if slides else None

    def _fallback_slides(self, title: str, count: int) -> list[dict]:
        return [
            {"title": f"الشريحة {i+1}" if i > 0 else title, "content": f"محتوى الشريحة {i+1}"}
            for i in range(count)
        ]
