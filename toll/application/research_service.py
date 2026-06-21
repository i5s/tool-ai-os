from __future__ import annotations

import logging
from typing import Any

from ..core.ai import AI
from ..core.connection_manager import ConnectionManager
from ..core.feature_flags import FeatureFlags
from ..core.provider_selector import ProviderSelector
from ..engine.renderers.preview_renderer import PreviewRenderer
from ..model.artifact import Artifact, ArtifactStatus, ArtifactType
from ..operations.usage_service import UsageService
from ..ports.research_source import (
    CitationStyle,
    ResearchQuery,
    ResearchSource,
)
from ..research.citation_engine import CitationEngine
from ..research.source_manager import SourceManager
from ..research.web_researcher import WebResearcher
from .artifact_service import ArtifactService
from .notebook_service import NotebookService

logger = logging.getLogger(__name__)


class ResearchService:
    def __init__(
        self,
        artifact_service: ArtifactService,
        selector: ProviderSelector,
        cm: ConnectionManager,
        flags: FeatureFlags | None = None,
        prompt_intelligence: Any = None,
    ):
        self.artifact_service = artifact_service
        self.selector = selector
        self.cm = cm
        self.flags = flags or FeatureFlags(cm=cm)
        self.ai = AI(cm=cm)
        self.preview = PreviewRenderer()
        self.citation_engine = CitationEngine()
        self.source_manager = SourceManager(
            cm=cm, citation_engine=self.citation_engine
        )
        self.prompt_intelligence = prompt_intelligence
        self.usage = UsageService(cm)

    def execute(self, plan: dict, metadata: dict | None = None) -> dict:
        topic = plan.get("title", plan.get("intent", "research"))
        style = plan.get("style", "apa")
        max_sources = plan.get("max_sources", 10)

        pie_profile_id = None
        if self.prompt_intelligence and self.flags.is_enabled("prompt_intelligence", default=False):
            pkg = self.prompt_intelligence.resolve(
                topic, media_type="text", execution_profile_id="research"
            )
            model_id = pkg.model_id or None
            pie_profile_id = pkg.profile_id
        else:
            model_id = None

        providers = self._get_providers()
        query = ResearchQuery(
            query=topic,
            max_sources=max_sources,
            style=style,
        )

        all_sources = self.source_manager.collect(query, providers)
        notebook_sources = self._include_notebook_sources(metadata)
        all_sources = notebook_sources + all_sources if notebook_sources else all_sources
        if not all_sources:
            synopsis = self._fallback_synthesis(topic)
            sources_data = []
            citations = []
        else:
            sources_data = [s.to_dict() for s in all_sources]
            citations = self.citation_engine.format_batch(
                all_sources, style
            )
            synopsis = self._synthesize(all_sources, topic, model_id=model_id)
        key_findings = self._extract_findings(synopsis)
        has_notebook = bool(notebook_sources)

        artifact = Artifact(
            id="",
            type=ArtifactType.RESEARCH,
            status=ArtifactStatus.DRAFT,
            title=topic,
            content={
                "query": topic,
                "sources": sources_data,
                "source_count": len(sources_data),
                "citations": citations,
                "citation_count": len(citations),
                "synopsis": synopsis,
                "key_findings": key_findings,
                "style": style,
                "notebook_sources": has_notebook,
            },
            provider=",".join(p.name for p in providers),
            intent=ArtifactType.RESEARCH,
            workflow_id=metadata.get("workflow_id") if metadata else None,
            conversation_id=(
                metadata.get("conversation_id") if metadata else None
            ),
        )

        rendered = self._render_research(topic, sources_data, citations, synopsis, key_findings)
        artifact = self.artifact_service.create(artifact, rendered)

        preview_html = self.preview.research_preview(artifact)
        preview_json = self.preview.json_preview(artifact)
        self.artifact_service.write_preview(artifact, preview_html, preview_json)

        self._store_sources(sources_data, artifact.id, style)

        if self.flags.is_enabled("research_memory_auto_index"):
            try:
                from ..research.memory_service import ResearchMemoryService
                rms = ResearchMemoryService(cm=self.cm)
                ws_type = metadata.get("workspace_type") if metadata else None
                ws_id = metadata.get("workspace_id") if metadata else None
                rms.index_research(
                    artifact=artifact,
                    sources=[ResearchSource(**s) for s in sources_data],
                    workspace_type=ws_type,
                    workspace_id=ws_id,
                )
            except Exception as e:
                logger.warning("Research memory indexing failed: %s", e)

        if pie_profile_id and self.prompt_intelligence:
            self.prompt_intelligence.record_success(
                pie_profile_id, model_id or ",".join(p.name for p in providers),
                topic, artifact_id=artifact.id,
            )

        if self.flags.is_enabled("operations_layer", default=True):
            self.usage.record(
                provider=",".join(p.name for p in providers),
                media_type="text", model_id=model_id or "",
                success=True, artifact_id=artifact.id,
                profile_id=pie_profile_id,
            )

        return {
            "artifact_id": artifact.id,
            "type": ArtifactType.RESEARCH.value,
            "title": topic,
            "source_count": len(sources_data),
            "citation_count": len(citations),
            "preview_url": artifact.preview_url,
            "rendered_path": artifact.rendered_path,
        }

    def execute_quick(
        self, plan: dict, metadata: dict | None = None
    ) -> dict:
        topic = plan.get("title", plan.get("intent", "research"))
        providers = self._get_providers()
        query = ResearchQuery(query=topic, max_sources=3)
        all_sources = self.source_manager.collect(query, providers)
        sources_data = [s.to_dict() for s in all_sources]

        return {
            "type": "research_quick",
            "title": topic,
            "sources": sources_data,
            "source_count": len(sources_data),
        }

    def execute_deep(
        self, plan: dict, metadata: dict | None = None
    ) -> dict:
        return self.execute(plan, metadata)

    def _get_providers(self) -> list:
        providers = []
        if self.flags.is_enabled("research_provider"):
            providers.append(WebResearcher())
        return providers

    def _include_notebook_sources(self, metadata: dict | None) -> list[ResearchSource]:
        if not metadata or "notebook_id" not in metadata:
            return []
        notebook_id = metadata["notebook_id"]
        try:
            svc = NotebookService(
                artifact_service=self.artifact_service,
                cm=self.cm,
                flags=self.flags,
                ai=self.ai,
            )
            sources = svc.list_sources(notebook_id)
            if not sources:
                return []
            from ..adapters.notebooks.notebooklm import NotebookLMResearchAdapter
            adapter = NotebookLMResearchAdapter(provider=None)
            return [
                ResearchSource(
                    title=s.title,
                    url=s.file_path,
                    source_type="notebook",
                    provider="notebooklm",
                    relevance_score=0.8,
                    confidence_score=1.0,
                    citation=s.title,
                    abstract="",
                )
                for s in sources
            ]
        except Exception as e:
            logger.warning("Notebook source inclusion failed: %s", e)
            return []

    def _synthesize(
        self, sources: list[ResearchSource], topic: str,
        model_id: str | None = None,
    ) -> str:
        try:
            source_list = "\n".join(
                f"- {s.title} ({s.authors[0] if s.authors else 'Unknown'}, {s.year or 'n.d.'})"
                for s in sources[:5]
            )
            prompt = (
                f"اكتب ملخصاً بالعربية عن '{topic}' بناءً على المصادر التالية:\n\n"
                f"{source_list}\n\n"
                f"الملخص يجب أن يكون فقرة واحدة مترابطة تغطي النقاط الرئيسية."
            )
            return self.ai.ask(prompt, provider_name=model_id) if model_id else self.ai.ask(prompt)
        except Exception as e:
            logger.warning("Synthesis failed: %s", e)
            return self._fallback_synthesis(topic)

    def _fallback_synthesis(self, topic: str) -> str:
        return f"موضوع البحث: {topic}. لم يتم العثور على مصادر كافية لتوليد ملخص."

    def _extract_findings(self, synopsis: str) -> list[str]:
        if not synopsis:
            return []
        sentences = [
            s.strip()
            for s in synopsis.replace("،", ".").replace(".", ".").split(".")
            if len(s.strip()) > 20
        ]
        return sentences[:3]

    def _render_research(
        self,
        topic: str,
        sources: list[dict],
        citations: list[str],
        synopsis: str,
        key_findings: list[str],
    ) -> str:
        src_rows = "".join(
            f"""<tr>
              <td>{s.get('title', '')}</td>
              <td>{', '.join(s.get('authors', []))}</td>
              <td>{s.get('year', '') or ''}</td>
              <td>{s.get('source_type', '')}</td>
            </tr>"""
            for s in sources
        )
        cite_list = "".join(
            f"<li>{c}</li>" for c in citations
        )
        kf_list = "".join(
            f"<li>{k}</li>" for k in key_findings
        )
        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{topic} — بحث</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:system-ui,'Times New Roman',serif; background:#f8f6f0; color:#1a1a2e; padding:40px; }}
.container {{ max-width:960px; margin:auto; background:#fff; padding:48px; border-radius:8px; box-shadow:0 2px 20px rgba(0,0,0,.06); }}
h1 {{ font-size:2rem; margin-bottom:8px; border-bottom:3px solid #1a365d; padding-bottom:12px; }}
h2 {{ font-size:1.3rem; margin:28px 0 12px; color:#1a365d; }}
.meta {{ color:#64748b; font-size:.9rem; margin-bottom:24px; }}
.synopsis {{ background:#f8fafc; padding:20px; border-radius:8px; line-height:1.9; margin:16px 0; }}
.kf {{ background:#f0fdf4; padding:16px 24px; border-radius:8px; margin:16px 0; }}
.kf li {{ margin:6px 0; line-height:1.7; }}
table {{ width:100%; border-collapse:collapse; margin:16px 0; font-size:.9rem; }}
th, td {{ border:1px solid #e2e8f0; padding:10px 12px; text-align:right; }}
th {{ background:#f1f5f9; color:#475569; font-weight:600; }}
tr:nth-child(even) {{ background:#fafafa; }}
.citations {{ background:#f8fafc; padding:16px 24px; border-radius:8px; }}
.citations li {{ margin:8px 0; line-height:1.7; font-size:.9rem; }}
.footer {{ margin-top:32px; padding-top:16px; border-top:1px solid #e2e8f0; color:#94a3b8; font-size:.8rem; text-align:center; }}
</style>
</head>
<body>
<div class="container">
  <h1>{topic}</h1>
  <div class="meta">{len(sources)} مصادر • {len(citations)} استشهاد</div>
  {f'<div class="synopsis"><strong>الملخص:</strong><br>{synopsis}</div>' if synopsis else ''}
  {f'<div class="kf"><strong>النتائج الرئيسية:</strong><ul>{kf_list}</ul></div>' if kf_list else ''}
  <h2>المصادر</h2>
  <table><thead><tr><th>العنوان</th><th>المؤلفون</th><th>السنة</th><th>النوع</th></tr></thead><tbody>{src_rows}</tbody></table>
  {f'<h2>الاستشهادات</h2><ol class="citations">{cite_list}</ol>' if cite_list else ''}
  <div class="footer">تم التوليد بواسطة تول v1.0.0 — Research Layer</div>
</div>
</body>
</html>"""

    def _store_sources(
        self,
        sources_data: list[dict],
        artifact_id: str,
        style: str,
    ):
        for sd in sources_data:
            source = ResearchSource(
                title=sd.get("title", ""),
                url=sd.get("url"),
                authors=sd.get("authors", []),
                year=sd.get("year"),
                citation=sd.get("citation", ""),
                relevance_score=sd.get("relevance_score", 0.0),
                confidence_score=sd.get("confidence_score", 0.0),
                source_type=sd.get("source_type"),
                doi=sd.get("doi"),
                journal=sd.get("journal"),
                abstract=sd.get("abstract"),
                provider=sd.get("provider", ""),
                provider_source_id=sd.get("provider_source_id"),
                citation_count=sd.get("citation_count", 0),
                language=sd.get("language", "en"),
                tags=sd.get("tags", []),
            )
            self.source_manager.store(source, artifact_id)
