from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.core.registry import ProviderRegistry
from toll.core.settings import Settings
from toll.model_registry.service import ModelRegistryService
from toll.prompt.profile_service import ExecutionProfileService, PromptProfileService
from toll.prompt.engine import PromptIntelligenceEngine
from api.dependencies import get_connection_manager

router = APIRouter()


class CreateProfileRequest(BaseModel):
    id: Optional[str] = None
    name: str
    media_types: list[str] = ["image"]
    template: str = ""
    default_params: dict = {}
    compatible_models: list[str] = []
    tags: list[str] = []


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    media_types: Optional[list[str]] = None
    template: Optional[str] = None
    default_params: Optional[dict] = None
    compatible_models: Optional[list[str]] = None
    weight_criteria: Optional[dict] = None
    tags: Optional[list[str]] = None
    enabled: Optional[bool] = None


class ResolveRequest(BaseModel):
    user_input: str
    media_type: str = "image"
    execution_profile_id: str = ""
    model_id: Optional[str] = None


def _get_profile_service(cm: ConnectionManager) -> PromptProfileService:
    flags = FeatureFlags(cm=cm)
    return PromptProfileService(cm=cm, flags=flags)


@router.get("/prompt/profiles")
def list_profiles(
    media_type: Optional[str] = None,
    tag: Optional[str] = None,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_profile_service(cm)
    return svc.list(media_type=media_type, tag=tag)


@router.get("/prompt/profiles/{profile_id}")
def get_profile(
    profile_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_profile_service(cm)
    result = svc.get(profile_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail="Profile not found")
    return result


@router.post("/prompt/profiles")
def create_profile(
    req: CreateProfileRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_profile_service(cm)
    return svc.create(req.dict())


@router.put("/prompt/profiles/{profile_id}")
def update_profile(
    profile_id: str,
    req: UpdateProfileRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_profile_service(cm)
    result = svc.update(profile_id, req.dict())
    if not result["success"]:
        raise HTTPException(status_code=404, detail="Profile not found")
    return result


@router.delete("/prompt/profiles/{profile_id}")
def delete_profile(
    profile_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_profile_service(cm)
    result = svc.delete(profile_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail="Profile not found")
    return result


@router.get("/prompt/profiles/{profile_id}/versions")
def get_profile_versions(
    profile_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_profile_service(cm)
    return svc.get_version_history(profile_id)


@router.get("/prompt/execution-profiles")
def list_execution_profiles():
    svc = ExecutionProfileService()
    return svc.list()


@router.get("/prompt/execution-profiles/{profile_id}")
def get_execution_profile(profile_id: str):
    svc = ExecutionProfileService()
    return svc.get(profile_id)


@router.post("/prompt/resolve")
def resolve_prompt(
    req: ResolveRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    flags = FeatureFlags(cm=cm)
    if not flags.is_enabled("prompt_intelligence", default=False):
        raise HTTPException(status_code=403, detail="Prompt Intelligence is disabled")
    registry = ProviderRegistry(Settings(cm=cm))
    model_registry = ModelRegistryService(cm=cm, flags=flags)
    engine = PromptIntelligenceEngine(
        cm=cm, flags=flags, registry=registry,
        model_registry=model_registry,
    )
    pkg = engine.resolve(
        user_input=req.user_input,
        media_type=req.media_type,
        execution_profile_id=req.execution_profile_id,
        model_id=req.model_id,
    )
    return {
        "prompt": pkg.prompt,
        "model_id": pkg.model_id,
        "profile_id": pkg.profile_id,
        "execution_profile_id": pkg.execution_profile_id,
        "prompt_version": pkg.prompt_version,
        "params": pkg.params,
        "debug_info": pkg.debug_info,
    }
