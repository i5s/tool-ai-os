from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List

from toll.analytics.models import AgentMetrics
from toll.analytics.service import AnalyticsService
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from api.dependencies import get_connection_manager

router = APIRouter()


def _require_flag(cm: ConnectionManager):
    flags = FeatureFlags(cm=cm)
    if not flags.is_enabled("agent_analytics"):
        raise HTTPException(status_code=404, detail="Not found")
    return flags


def _get_service(cm: ConnectionManager) -> AnalyticsService:
    return AnalyticsService(cm)


def _metrics_to_dict(m: AgentMetrics) -> dict:
    return {
        "agent_id": m.agent_id,
        "agent_name": m.agent_name,
        "total_executions": m.total_executions,
        "successful_executions": m.successful_executions,
        "failed_executions": m.failed_executions,
        "success_rate": m.success_rate,
        "average_duration_ms": m.average_duration_ms,
        "council_participation_count": m.council_participation_count,
        "learning_entries_created": m.learning_entries_created,
    }


@router.get("/analytics/agents")
def list_agent_metrics(cm: ConnectionManager = Depends(get_connection_manager)):
    _require_flag(cm)
    service = _get_service(cm)
    return [_metrics_to_dict(m) for m in service.get_all_agent_metrics()]


@router.get("/analytics/agents/top")
def get_top_agents(limit: int = 5, cm: ConnectionManager = Depends(get_connection_manager)):
    _require_flag(cm)
    service = _get_service(cm)
    return [_metrics_to_dict(m) for m in service.get_top_agents(limit=limit)]


@router.get("/analytics/agents/{agent_id}")
def get_agent_metrics(agent_id: str, cm: ConnectionManager = Depends(get_connection_manager)):
    _require_flag(cm)
    service = _get_service(cm)
    result = service.get_agent_metrics(agent_id)
    if not result:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _metrics_to_dict(result)
