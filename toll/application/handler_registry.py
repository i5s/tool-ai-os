from __future__ import annotations

from ..core.connection_manager import ConnectionManager
from ..core.feature_flags import FeatureFlags
from ..core.provider_selector import ProviderSelector
from ..core.registry import ProviderRegistry
from ..core.settings import Settings
from ..workflow.engine import WorkflowEngine
from .artifact_service import ArtifactService
from .carousel_service import CarouselService
from .report_service import ReportService
from .presentation_service import PresentationService
from .opendesign_service import OpenDesignService
from .research_service import ResearchService
from .notebook_service import NotebookService


def register_handlers(
    wf_engine: WorkflowEngine,
    cm: ConnectionManager,
):
    settings = Settings(cm=cm)
    registry = ProviderRegistry(settings)
    flags = FeatureFlags(cm=cm)
    selector = ProviderSelector(registry, settings, flags)
    artifact_service = ArtifactService(cm)

    if flags.is_enabled("carousel_engine"):
        svc = CarouselService(artifact_service, selector, cm)
        wf_engine.register_handler("carousel", svc.execute)

    if flags.is_enabled("report_engine"):
        svc = ReportService(artifact_service, selector, cm)
        wf_engine.register_handler("report", svc.execute)

    if flags.is_enabled("presentation_engine"):
        svc = PresentationService(artifact_service, selector, cm)
        wf_engine.register_handler("presentation", svc.execute)

    if flags.is_enabled("opendesign_integration"):
        svc = OpenDesignService(artifact_service)
        wf_engine.register_handler("opendesign_push", svc.push_from_workflow)

    if flags.is_enabled("research_provider"):
        svc = ResearchService(artifact_service, selector, cm, flags)
        wf_engine.register_handler("research", svc.execute)
        wf_engine.register_handler("research_quick", svc.execute_quick)
        wf_engine.register_handler("research_deep", svc.execute_deep)

    if flags.is_enabled("notebooklm_enabled"):
        from toll.adapters.notebooks.notebooklm import NotebookLMProvider
        notebook_provider = NotebookLMProvider(cm=cm)
        svc = NotebookService(artifact_service, cm, flags, notebook_provider=notebook_provider)
        wf_engine.register_handler(
            "notebook_upload",
            lambda p, _m, _s=svc: _s.upload_source(
                notebook_id=p["notebook_id"], content=p["content"],
                file_name=p["file_name"], title=p.get("title", ""),
            ),
        )
        wf_engine.register_handler(
            "notebook_notes",
            lambda p, _m, _s=svc: _s.create_notes(
                notebook_id=p["notebook_id"], source_ids=p.get("source_ids"),
            ),
        )
        wf_engine.register_handler(
            "notebook_query",
            lambda p, _m, _s=svc: _s.query(
                notebook_id=p["notebook_id"], question=p["question"],
            ),
        )
