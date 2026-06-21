from __future__ import annotations

from ..adapters.media.ollama import OllamaMediaAdapter
from ..adapters.media.replicate import ReplicateMediaAdapter
from ..core.connection_manager import ConnectionManager
from ..core.feature_flags import FeatureFlags
from ..core.provider_selector import ProviderSelector
from ..core.registry import ProviderRegistry
from ..core.settings import Settings
from ..workflow.engine import WorkflowEngine
from .artifact_service import ArtifactService
from .carousel_service import CarouselService
from .media_service import MediaService
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

    if flags.is_enabled("media_generation", default=True):
        if flags.is_enabled("media_image", default=True):
            registry.register_media("replicate", ReplicateMediaAdapter())
            registry.register_media("ollama", OllamaMediaAdapter())
        from ..model_registry.service import ModelRegistryService
        model_registry = ModelRegistryService(cm=cm, flags=flags)
        svc = MediaService(cm, registry, selector, flags,
                           model_registry=model_registry)
        wf_engine.register_handler("media_generate", svc.generate)

    if flags.is_enabled("benchmark_lab", default=False):
        from ..benchmark.service import BenchmarkService
        bench_svc = BenchmarkService(cm=cm, registry=registry, flags=flags)
        wf_engine.register_handler("benchmark_run", bench_svc.execute)
        wf_engine.register_handler("benchmark_create_suite", bench_svc.create_suite)
        wf_engine.register_handler("benchmark_list_suites", bench_svc.list_suites)
        wf_engine.register_handler("benchmark_model_scores", bench_svc.model_scores)

    if flags.is_enabled("prompt_intelligence", default=False):
        from ..model_registry.service import ModelRegistryService as _ModelRegistryService
        from ..prompt.engine import PromptIntelligenceEngine
        _mr = _ModelRegistryService(cm=cm, flags=flags)
        _pie = PromptIntelligenceEngine(cm=cm, flags=flags, registry=registry,
                                        model_registry=_mr)
        wf_engine.register_handler("prompt_intelligence", lambda p, _m, _e=_pie: (
            _e.resolve(
                user_input=p.get("user_input", ""),
                media_type=p.get("media_type", "image"),
                execution_profile_id=p.get("execution_profile_id", ""),
                model_id=p.get("model_id"),
            )
        ))
