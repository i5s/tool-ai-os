from __future__ import annotations

import logging
import time

from ..core.registry import ProviderRegistry
from ..ports.media import MediaRequest
from .quality_scorer import QualityScorer
from .repository import BenchmarkRepository

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    def __init__(
        self,
        repo: BenchmarkRepository,
        registry: ProviderRegistry,
        scorer: QualityScorer | None = None,
    ):
        self.repo = repo
        self.registry = registry
        self.scorer = scorer or QualityScorer()
        self.scorer.register_criterion("latency_ms", weight=0.3)
        self.scorer.register_criterion("file_size_bytes", weight=0.2)
        self.scorer.register_criterion("no_error", weight=0.5)

    def run_suite(self, suite_id: str, model_id: str) -> dict:
        suite = self.repo.get_suite(suite_id)
        if not suite:
            return {"success": False, "error": "Suite not found"}

        media_port = self._get_model_port(model_id)
        if not media_port:
            return {"success": False, "error": f"No port available for model {model_id}"}

        results: list[dict] = []
        for idx, prompt in enumerate(suite.prompts):
            run_row = self.repo.create_run(
                model_id=model_id,
                prompt=prompt,
                media_type=suite.media_type,
                suite_id=suite_id,
                prompt_index=idx,
            )
            start = time.monotonic()
            try:
                request = MediaRequest(prompt=prompt, media_type=suite.media_type)
                result = media_port.generate(request)
                elapsed_ms = int((time.monotonic() - start) * 1000)

                run_data = {
                    "provider_latency_ms": elapsed_ms,
                    "file_size_bytes": result.file_size_bytes,
                    "error": result.error,
                }

                quality = self.scorer.score(run_data)
                self.repo.update_run(
                    run_row.id,
                    provider_latency_ms=elapsed_ms,
                    total_duration_ms=elapsed_ms,
                    file_size_bytes=result.file_size_bytes,
                    quality_score_auto=quality,
                    error=result.error or None,
                )
            except Exception as e:
                elapsed_ms = int((time.monotonic() - start) * 1000)
                logger.warning("Benchmark prompt %d failed: %s", idx, e)
                self.repo.update_run(
                    run_row.id,
                    total_duration_ms=elapsed_ms,
                    error=str(e),
                )

            updated = self.repo.get_run(run_row.id)
            if updated:
                results.append({
                    "run_id": updated.id,
                    "prompt": prompt,
                    "quality_score": updated.quality_score_auto,
                    "error": updated.error,
                })

        scores = self.repo.avg_scores(model_id)
        return {
            "success": True,
            "suite_id": suite_id,
            "model_id": model_id,
            "prompts_completed": len(results),
            "results": results,
            "aggregate": scores,
        }

    def _get_model_port(self, model_id: str) -> object | None:
        for name, port in self.registry.all_media().items():
            if port.is_available():
                return port
        return None

    def run_prompt(self, model_id: str, prompt: str, media_type: str = "image") -> dict:
        media_port = self._get_model_port(model_id)
        if not media_port:
            return {"success": False, "error": "No media provider available"}

        run_row = self.repo.create_run(
            model_id=model_id,
            prompt=prompt,
            media_type=media_type,
        )

        start = time.monotonic()
        try:
            request = MediaRequest(prompt=prompt, media_type=media_type)
            result = media_port.generate(request)
            elapsed_ms = int((time.monotonic() - start) * 1000)

            run_data = {
                "provider_latency_ms": elapsed_ms,
                "file_size_bytes": result.file_size_bytes,
                "error": result.error,
            }
            quality = self.scorer.score(run_data)
            self.repo.update_run(
                run_row.id,
                provider_latency_ms=elapsed_ms,
                total_duration_ms=elapsed_ms,
                file_size_bytes=result.file_size_bytes,
                quality_score_auto=quality,
                error=result.error or None,
            )

            return {
                "success": result.success,
                "run_id": run_row.id,
                "quality_score": quality,
                "error": result.error,
            }
        except Exception as e:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            self.repo.update_run(run_row.id, total_duration_ms=elapsed_ms, error=str(e))
            return {"success": False, "run_id": run_row.id, "error": str(e)}
