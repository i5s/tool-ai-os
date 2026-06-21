from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.model_registry.service import ModelRegistryService
from api.dependencies import get_connection_manager

router = APIRouter()


class RegisterModelRequest(BaseModel):
    provider: str
    provider_model_id: str
    name: str
    description: str = ""
    media_types: list[str] = ["image"]
    tags: list[str] = []
    family: Optional[str] = None
    status: str = "active"
    cost_per_unit: Optional[float] = None
    cost_unit: Optional[str] = None


class UpdateModelRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    cost_per_unit: Optional[float] = None


def _get_service(cm: ConnectionManager) -> ModelRegistryService:
    flags = FeatureFlags(cm=cm)
    if not flags.is_enabled("model_registry", default=True):
        raise HTTPException(status_code=403, detail="Model Registry is disabled")
    return ModelRegistryService(cm=cm, flags=flags)


@router.get("/models")
def list_models(
    provider: Optional[str] = None,
    media_type: Optional[str] = None,
    status: Optional[str] = None,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_service(cm)
    models = svc.list(provider=provider, media_type=media_type, status=status)
    return {
        "total": len(models),
        "models": [
            {
                "id": m.id,
                "provider": m.provider,
                "provider_model_id": m.provider_model_id,
                "name": m.name,
                "description": m.description,
                "media_types": m.media_types,
                "tags": m.tags,
                "family": m.family,
                "status": m.status,
                "cost_per_unit": m.cost_per_unit,
                "cost_unit": m.cost_unit,
                "registered_at": m.registered_at,
            }
            for m in models
        ],
    }


@router.get("/models/providers")
def list_providers(
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_service(cm)
    providers = svc.list_providers()
    return {"providers": providers}


@router.get("/models/{model_id}")
def get_model(
    model_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_service(cm)
    m = svc.get(model_id)
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    return {
        "id": m.id,
        "provider": m.provider,
        "provider_model_id": m.provider_model_id,
        "name": m.name,
        "description": m.description,
        "media_types": m.media_types,
        "tags": m.tags,
        "family": m.family,
        "status": m.status,
        "cost_per_unit": m.cost_per_unit,
        "cost_unit": m.cost_unit,
        "registered_at": m.registered_at,
    }


@router.post("/models")
def register_model(
    req: RegisterModelRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_service(cm)
    try:
        m = svc.register({
            "provider": req.provider,
            "provider_model_id": req.provider_model_id,
            "name": req.name,
            "description": req.description,
            "media_types": req.media_types,
            "tags": req.tags,
            "family": req.family,
            "status": req.status,
            "cost_per_unit": req.cost_per_unit,
            "cost_unit": req.cost_unit,
        })
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {
        "id": m.id,
        "provider": m.provider,
        "name": m.name,
        "status": m.status,
    }


@router.put("/models/{model_id}")
def update_model(
    model_id: str,
    req: UpdateModelRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_service(cm)
    updates = {k: v for k, v in req.dict().items() if v is not None}
    m = svc.update(model_id, updates)
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    return {
        "id": m.id,
        "name": m.name,
        "status": m.status,
    }


@router.delete("/models/{model_id}")
def disable_model(
    model_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_service(cm)
    if not svc.disable(model_id):
        raise HTTPException(status_code=404, detail="Model not found")
    return {"id": model_id, "status": "disabled"}
