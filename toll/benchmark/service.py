from __future__ import annotations

import json
import logging

from ..core.connection_manager import ConnectionManager
from ..core.feature_flags import FeatureFlags
from ..core.registry import ProviderRegistry
from .quality_scorer import QualityScorer
from .repository import BenchmarkRepository
from .runner import BenchmarkRunner

logger = logging.getLogger(__name__)


class BenchmarkService:
    def __init__(
        self,
        cm: ConnectionManager,
        registry: ProviderRegistry,
        flags: FeatureFlags,
    ):
        self.repo = BenchmarkRepository(cm)
        self.runner = BenchmarkRunner(self.repo, registry)

    def create_suite(self, params: dict) -> dict:
        name = params.get("name", "")
        if not name:
            return {"success": False, "error": "Suite name required"}
        prompts = params.get("prompts", [])
        if not prompts:
            return {"success": False, "error": "At least one prompt required"}
        media_type = params.get("media_type", "image")
        suite = self.repo.create_suite(
            name=name,
            prompts=prompts,
            media_type=media_type,
            description=params.get("description", ""),
        )
        return {
            "success": True,
            "suite_id": suite.id,
            "name": suite.name,
            "prompts": len(suite.prompts),
        }

    def list_suites(self) -> dict:
        suites = self.repo.list_suites()
        return {
            "success": True,
            "suites": [
                {
                    "id": s.id,
                    "name": s.name,
                    "prompts": len(s.prompts),
                    "media_type": s.media_type,
                    "created_at": s.created_at,
                }
                for s in suites
            ],
        }

    def get_suite(self, suite_id: str) -> dict:
        suite = self.repo.get_suite(suite_id)
        if not suite:
            return {"success": False, "error": "Suite not found"}
        return {
            "success": True,
            "suite": {
                "id": suite.id,
                "name": suite.name,
                "description": suite.description,
                "prompts": suite.prompts,
                "media_type": suite.media_type,
                "created_at": suite.created_at,
            },
        }

    def execute(self, params: dict) -> dict:
        suite_id = params.get("suite_id")
        model_id = params.get("model_id")
        prompt = params.get("prompt")

        if prompt:
            model_id = model_id or params.get("model_id", "replicate:flux-schnell")
            return self.runner.run_prompt(model_id, prompt)

        if suite_id and model_id:
            return self.runner.run_suite(suite_id, model_id)

        if not suite_id:
            return {"success": False, "error": "suite_id or prompt required"}

        return {"success": False, "error": "model_id required for suite execution"}

    def model_scores(self, model_id: str) -> dict:
        scores = self.repo.avg_scores(model_id)
        return {"success": True, "model_id": model_id, **scores}

    def list_runs(self, model_id: str | None = None) -> dict:
        runs = self.repo.list_runs(model_id=model_id)
        return {
            "success": True,
            "runs": [
                {
                    "id": r.id,
                    "model_id": r.model_id,
                    "prompt": r.prompt[:60],
                    "quality_score_auto": r.quality_score_auto,
                    "error": r.error,
                    "created_at": r.created_at,
                }
                for r in runs
            ],
        }
