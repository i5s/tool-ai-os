from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional

from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.core.registry import ProviderRegistry
from toll.core.settings import Settings
from toll.model_registry.service import ModelRegistryService
from toll.operations.usage_service import UsageService
from toll.operations.cost_service import CostService
from toll.operations.storage_service import StorageService
from toll.operations.cleanup_service import CleanupService
from toll.operations.dashboard_service import ProviderDashboardService
from api.dependencies import get_connection_manager

router = APIRouter()


class RetentionPolicyRequest(BaseModel):
    id: Optional[str] = None
    name: str = "Default"
    retention_days: int = 4
    keep_metadata: bool = True
    enabled: bool = True
    workspace_type: Optional[str] = None
    workspace_id: Optional[str] = None
    media_type: Optional[str] = None


def _usage(cm):
    return UsageService(cm)


def _cost(cm):
    return CostService(cm)


def _storage(cm):
    return StorageService(cm)


def _cleanup(cm):
    return CleanupService(cm)


def _dashboard(cm):
    registry = ProviderRegistry(Settings(cm=cm))
    mr = ModelRegistryService(cm=cm, flags=FeatureFlags(cm=cm))
    return ProviderDashboardService(cm, registry, mr)


@router.get("/operations/usage/summary")
def usage_summary(
    days: int = Query(30, ge=1, le=365),
    cm: ConnectionManager = Depends(get_connection_manager),
):
    return _usage(cm).summary(days)


@router.get("/operations/usage/by-provider")
def usage_by_provider(
    days: int = Query(30, ge=1, le=365),
    cm: ConnectionManager = Depends(get_connection_manager),
):
    return {"providers": _usage(cm).by_provider(days)}


@router.get("/operations/usage/by-model")
def usage_by_model(
    days: int = Query(30, ge=1, le=365),
    cm: ConnectionManager = Depends(get_connection_manager),
):
    return {"models": _usage(cm).by_model(days)}


@router.get("/operations/usage/daily")
def usage_daily(
    days: int = Query(30, ge=1, le=365),
    cm: ConnectionManager = Depends(get_connection_manager),
):
    return {"daily": _usage(cm).daily_cost(days)}


@router.get("/operations/usage/recent")
def usage_recent(
    limit: int = Query(20, ge=1, le=100),
    cm: ConnectionManager = Depends(get_connection_manager),
):
    return {"entries": _usage(cm).recent(limit)}


@router.get("/operations/cost")
def cost_summary(
    days: int = Query(30, ge=1, le=365),
    cm: ConnectionManager = Depends(get_connection_manager),
):
    return _cost(cm).total(days)


@router.get("/operations/cost/daily")
def cost_daily(
    days: int = Query(30, ge=1, le=365),
    cm: ConnectionManager = Depends(get_connection_manager),
):
    return {"daily": _cost(cm).daily(days)}


@router.get("/operations/storage")
def storage_summary(
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _storage(cm)
    return {
        "summary": svc.summary(),
        "total_size_mb": svc.total_size_mb(),
    }


@router.get("/operations/storage/published")
def published_assets(
    limit: int = Query(50, ge=1, le=200),
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _storage(cm)
    return {"assets": svc.published_assets(limit),
            "total": len(svc.published_assets(limit))}


@router.get("/operations/storage/pending-cleanup")
def pending_cleanup(
    older_than_days: int = Query(4, ge=1, le=365),
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _storage(cm)
    return {"artifacts": svc.pending_cleanup(older_than_days)}


@router.get("/operations/storage/retention")
def list_retention_policies(
    cm: ConnectionManager = Depends(get_connection_manager),
):
    return {"policies": _storage(cm).retention_policies()}


@router.post("/operations/storage/retention")
def upsert_retention_policy(
    req: RetentionPolicyRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    return _storage(cm).upsert_retention_policy(
        policy_id=req.id, name=req.name,
        retention_days=req.retention_days,
        keep_metadata=req.keep_metadata,
        enabled=req.enabled,
        workspace_type=req.workspace_type,
        workspace_id=req.workspace_id,
        media_type=req.media_type,
    )


@router.delete("/operations/storage/retention/{policy_id}")
def delete_retention_policy(
    policy_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    _storage(cm).delete_retention_policy(policy_id)
    return {"id": policy_id, "deleted": True}


@router.get("/operations/cleanup/simulate")
def cleanup_simulate(
    cm: ConnectionManager = Depends(get_connection_manager),
):
    return _cleanup(cm).simulate()


@router.post("/operations/cleanup/execute")
def cleanup_execute(
    cm: ConnectionManager = Depends(get_connection_manager),
):
    return _cleanup(cm).execute()


@router.get("/operations/cleanup/log")
def cleanup_log(
    limit: int = Query(20, ge=1, le=100),
    cm: ConnectionManager = Depends(get_connection_manager),
):
    return {"entries": _cleanup(cm).log(limit)}


@router.get("/operations/providers")
def provider_summary(
    hours: int = Query(24, ge=1, le=720),
    cm: ConnectionManager = Depends(get_connection_manager),
):
    return {"providers": _dashboard(cm).summary(hours)}


@router.get("/operations/providers/{name}")
def provider_detail(
    name: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    result = _dashboard(cm).provider_detail(name)
    if not result:
        raise HTTPException(status_code=404, detail="Provider not found")
    return result
