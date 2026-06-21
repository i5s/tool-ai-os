from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from toll.benchmark.service import BenchmarkService
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.core.registry import ProviderRegistry
from toll.core.settings import Settings
from api.dependencies import get_connection_manager

router = APIRouter()


class CreateSuiteRequest(BaseModel):
    name: str
    description: str = ""
    prompts: list[str]
    media_type: str = "image"


class RunBenchmarkRequest(BaseModel):
    suite_id: Optional[str] = None
    model_id: Optional[str] = None
    prompt: Optional[str] = None
    media_type: str = "image"


def _get_service(cm: ConnectionManager) -> BenchmarkService:
    flags = FeatureFlags(cm=cm)
    if not flags.is_enabled("benchmark_lab", default=False):
        raise HTTPException(status_code=403, detail="Benchmark Lab is disabled")
    registry = ProviderRegistry(Settings(cm=cm))
    return BenchmarkService(cm=cm, registry=registry, flags=flags)


@router.post("/benchmark/suites")
def create_suite(
    req: CreateSuiteRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_service(cm)
    return svc.create_suite(req.dict())


@router.get("/benchmark/suites")
def list_suites(
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_service(cm)
    return svc.list_suites()


@router.get("/benchmark/suites/{suite_id}")
def get_suite(
    suite_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_service(cm)
    return svc.get_suite(suite_id)


@router.delete("/benchmark/suites/{suite_id}")
def delete_suite(
    suite_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_service(cm)
    from toll.benchmark.repository import BenchmarkRepository
    repo = BenchmarkRepository(cm)
    if not repo.delete_suite(suite_id):
        raise HTTPException(status_code=404, detail="Suite not found")
    return {"id": suite_id, "deleted": True}


@router.post("/benchmark/run")
def run_benchmark(
    req: RunBenchmarkRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_service(cm)
    return svc.execute(req.dict())


@router.get("/benchmark/runs")
def list_runs(
    model_id: Optional[str] = None,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_service(cm)
    return svc.list_runs(model_id=model_id)


@router.get("/benchmark/models/{model_id}/scores")
def model_scores(
    model_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_service(cm)
    return svc.model_scores(model_id)
