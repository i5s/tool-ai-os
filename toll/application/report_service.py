from __future__ import annotations

import logging
from typing import Any

from ..core.ai import AI
from ..core.connection_manager import ConnectionManager
from ..core.feature_flags import FeatureFlags
from ..core.provider_selector import ProviderSelector
from ..engine.renderers.preview_renderer import PreviewRenderer
from ..engine.renderers.report_renderer import ReportRenderer
from ..model.artifact import Artifact, ArtifactStatus, ArtifactType
from ..operations.usage_service import UsageService
from .artifact_service import ArtifactService

logger = logging.getLogger(__name__)


class ReportService:
    def __init__(self, artifact_service: ArtifactService, selector: ProviderSelector,
                 cm: ConnectionManager, flags: FeatureFlags | None = None,
                 prompt_intelligence: Any = None):
        self.artifact_service = artifact_service
        self.selector = selector
        self.cm = cm
        self.flags = flags or FeatureFlags(cm=cm)
        self.ai = AI(cm=cm)
        self.renderer = ReportRenderer()
        self.preview = PreviewRenderer()
        self.prompt_intelligence = prompt_intelligence
        self.usage = UsageService(cm)

    def execute(self, plan: dict, metadata: dict | None = None) -> dict:
        title = plan.get("title", plan.get("intent", "report"))
        style = plan.get("style", "academic")
        sections_list = plan.get("sections", None)

        pie_profile_id = None
        provider_name = self.selector.select(ArtifactType.REPORT)
        if not provider_name:
            return {"error": "No available provider for report generation"}

        prompt = self._build_prompt(title, style, sections_list)

        if self.prompt_intelligence and self.flags.is_enabled("prompt_intelligence", default=False):
            pkg = self.prompt_intelligence.resolve(
                title, media_type="text", execution_profile_id="academic_report",
                model_id=provider_name,
            )
            provider_name = pkg.model_id or provider_name
            pie_profile_id = pkg.profile_id

        try:
            raw = self.ai.ask(prompt, provider_name=provider_name)
        except RuntimeError as e:
            if pie_profile_id and self.prompt_intelligence:
                self.prompt_intelligence.record_failure(
                    pie_profile_id, provider_name, str(e),
                )
            if self.flags.is_enabled("operations_layer", default=True):
                self.usage.record(
                    provider=provider_name, media_type="text",
                    model_id=provider_name, success=False,
                    error=str(e), profile_id=pie_profile_id,
                )
            return {"error": str(e)}

        sections = self._parse_sections(raw) or self._fallback_sections(title, sections_list)

        artifact = Artifact(
            id="",
            type=ArtifactType.REPORT,
            status=ArtifactStatus.DRAFT,
            title=title,
            content={"sections": sections, "style": style},
            provider=provider_name,
            intent=ArtifactType.REPORT,
            workflow_id=metadata.get("workflow_id") if metadata else None,
            conversation_id=metadata.get("conversation_id") if metadata else None,
        )

        rendered = self.renderer.render(title, sections)
        artifact = self.artifact_service.create(artifact, rendered)

        if pie_profile_id and self.prompt_intelligence:
            self.prompt_intelligence.record_success(
                pie_profile_id, provider_name, prompt,
                artifact_id=artifact.id,
            )

        if self.flags.is_enabled("operations_layer", default=True):
            self.usage.record(
                provider=provider_name, media_type="text",
                model_id=provider_name, success=True,
                artifact_id=artifact.id, profile_id=pie_profile_id,
            )

        preview_html = self.preview.report_preview(artifact)
        preview_json = self.preview.json_preview(artifact)
        self.artifact_service.write_preview(artifact, preview_html, preview_json)

        return {
            "artifact_id": artifact.id,
            "type": ArtifactType.REPORT.value,
            "title": title,
            "sections": len(sections),
            "preview_url": artifact.preview_url,
            "rendered_path": artifact.rendered_path,
        }

    def _build_prompt(self, title: str, style: str, sections: list[str] | None) -> str:
        secs = ", ".join(sections) if sections else "Executive Summary, Introduction, Analysis, Recommendations, Conclusion"
        return (
            f"Write a {style} report titled '{title}' in Arabic.\n"
            f"Sections: {secs}\n"
            f"Return each section as exactly:\n"
            f"SECTION | Heading | Body\n"
            f"Then for subsections:\n"
            f"SUB | Subheading | Body\n"
        )

    def _parse_sections(self, raw: str) -> list[dict] | None:
        sections = []
        current = None
        for line in raw.strip().split("\n"):
            line = line.strip()
            if line.startswith("SECTION |"):
                parts = line.split("|")
                if len(parts) >= 3:
                    current = {
                        "heading": parts[1].strip(),
                        "body": "|".join(parts[2:]).strip(),
                        "subsections": [],
                    }
                    sections.append(current)
            elif line.startswith("SUB |") and current is not None:
                parts = line.split("|")
                if len(parts) >= 3:
                    current["subsections"].append({
                        "subheading": parts[1].strip(),
                        "body": "|".join(parts[2:]).strip(),
                    })
        return sections if sections else None

    def _fallback_sections(self, title: str, sections: list[str] | None) -> list[dict]:
        return [
            {"heading": s, "body": f"محتوى {s}", "subsections": []}
            for s in (sections or ["الملخص", "المقدمة", "التحليل", "التوصيات", "الخاتمة"])
        ]
