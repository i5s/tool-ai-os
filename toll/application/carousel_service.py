from __future__ import annotations

import json
import logging

from ..core.ai import AI
from ..core.connection_manager import ConnectionManager
from ..core.provider_selector import ProviderSelector
from ..engine.renderers.carousel_renderer import CarouselRenderer
from ..engine.renderers.preview_renderer import PreviewRenderer
from ..model.artifact import Artifact, ArtifactStatus, ArtifactType
from .artifact_service import ArtifactService

logger = logging.getLogger(__name__)


class CarouselService:
    def __init__(self, artifact_service: ArtifactService, selector: ProviderSelector, cm: ConnectionManager):
        self.artifact_service = artifact_service
        self.selector = selector
        self.cm = cm
        self.ai = AI(cm=cm)
        self.renderer = CarouselRenderer()
        self.preview = PreviewRenderer()

    def execute(self, plan: dict, metadata: dict | None = None) -> dict:
        topic = plan.get("title", plan.get("intent", "carousel"))
        slides_count = plan.get("slides", 4)
        style = plan.get("style", "modern")

        provider_name = self.selector.select(ArtifactType.CAROUSEL)
        if not provider_name:
            return {"error": "No available provider for carousel generation"}

        prompt = self._build_prompt(topic, slides_count, style)
        try:
            raw = self.ai.ask(prompt, provider_name=provider_name)
        except RuntimeError as e:
            return {"error": str(e)}

        slides = self._parse_slides(raw) or self._fallback_slides(topic, slides_count)

        artifact = Artifact(
            id="",
            type=ArtifactType.CAROUSEL,
            status=ArtifactStatus.DRAFT,
            title=topic,
            content={"slides": slides, "style": style, "slide_count": slides_count},
            provider=provider_name,
            intent=ArtifactType.CAROUSEL,
            workflow_id=metadata.get("workflow_id") if metadata else None,
            conversation_id=metadata.get("conversation_id") if metadata else None,
        )

        rendered = self.renderer.render(topic, slides)
        artifact = self.artifact_service.create(artifact, rendered)

        preview_html = self.preview.carousel_preview(artifact)
        preview_json = self.preview.json_preview(artifact)
        self.artifact_service.write_preview(artifact, preview_html, preview_json)

        return {
            "artifact_id": artifact.id,
            "type": ArtifactType.CAROUSEL.value,
            "title": topic,
            "slides": len(slides),
            "preview_url": artifact.preview_url,
            "rendered_path": artifact.rendered_path,
        }

    def _build_prompt(self, topic: str, count: int, style: str) -> str:
        return (
            f"Write {count} slides for a carousel about '{topic}' in Arabic.\n"
            f"Style: {style}.\n"
            f"Return each slide as exactly one line in this format:\n"
            f"SLIDE | Title | Subtitle | Content\n"
        )

    def _parse_slides(self, raw: str) -> list[dict] | None:
        slides = []
        for line in raw.strip().split("\n"):
            line = line.strip()
            if line.startswith("SLIDE |"):
                parts = line.split("|")
                if len(parts) >= 4:
                    slides.append({
                        "title": parts[1].strip(),
                        "subtitle": parts[2].strip(),
                        "content": "|".join(parts[3:]).strip(),
                    })
        return slides if slides else None

    def _fallback_slides(self, topic: str, count: int) -> list[dict]:
        return [
            {"title": topic, "subtitle": f"الجزء {i+1}", "content": f"محتوى الجزء {i+1}"}
            for i in range(count)
        ]
