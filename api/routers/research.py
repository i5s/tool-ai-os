from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from toll.application.research_service import ResearchService
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.core.provider_selector import ProviderSelector
from toll.core.registry import ProviderRegistry
from toll.core.settings import Settings
from toll.application.artifact_service import ArtifactService
from api.dependencies import get_connection_manager

router = APIRouter()


class ResearchRequest(BaseModel):
    topic: str
    style: str = "apa"
    max_sources: int = 10
    mode: str = "standard"  # standard | quick | deep
    metadata: Optional[dict] = None


class ResearchResponse(BaseModel):
    artifact_id: str
    type: str
    title: str
    source_count: int
    citation_count: int
    preview_url: Optional[str] = None
    rendered_path: Optional[str] = None


def _get_research_service(cm: ConnectionManager) -> ResearchService:
    settings = Settings(cm=cm)
    registry = ProviderRegistry(settings)
    flags = FeatureFlags(cm=cm)
    selector = ProviderSelector(registry, settings, flags)
    artifact_service = ArtifactService(cm)
    return ResearchService(artifact_service, selector, cm, flags)


@router.post("/research")
def create_research(
    req: ResearchRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")
    svc = _get_research_service(cm)
    plan = {
        "title": req.topic,
        "style": req.style,
        "max_sources": req.max_sources,
    }
    if req.mode == "quick":
        result = svc.execute_quick(plan, req.metadata)
    elif req.mode == "deep":
        result = svc.execute_deep(plan, req.metadata)
    else:
        result = svc.execute(plan, req.metadata)
    return ResearchResponse(**result)


@router.get("/research/styles")
def list_styles():
    return {
        "styles": [
            {"id": "apa", "label": "APA (7th ed.)"},
            {"id": "mla", "label": "MLA (9th ed.)"},
            {"id": "ieee", "label": "IEEE"},
            {"id": "chicago_notes", "label": "Chicago (Notes & Biblio)"},
            {"id": "chicago_date", "label": "Chicago (Author-Date)"},
            {"id": "vancouver", "label": "Vancouver"},
        ]
    }


@router.get("/research/modes")
def list_modes():
    return {
        "modes": [
            {
                "id": "standard",
                "label": "البحث القياسي",
                "description": "جمع المصادر + الاستشهادات + الملخص بالذكاء الاصطناعي",
            },
            {
                "id": "quick",
                "label": "بحث سريع",
                "description": "جمع سريع للمصادر بدون تخزين أو تلخيص",
            },
            {
                "id": "deep",
                "label": "بحث معمق",
                "description": "نفس البحث القياسي مع مصادر إضافية وأعمق",
            },
        ]
    }
