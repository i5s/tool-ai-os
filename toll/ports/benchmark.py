from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BenchmarkRun:
    id: str
    model_id: str
    prompt: str
    media_type: str
    provider_latency_ms: int = 0
    total_duration_ms: int = 0
    file_size_bytes: int = 0
    quality_score_auto: float = 0.0
    quality_score_human: float | None = None
    cost_cents: float = 0.0
    seed: int | None = None
    output_storage_key: str | None = None
    content_type: str = ""
    width: int | None = None
    height: int | None = None
    duration_ms: int | None = None
    suite_id: str | None = None
    prompt_index: int | None = None
    error: str | None = None
    created_at: str = ""


@dataclass
class BenchmarkSuite:
    id: str
    name: str
    description: str = ""
    prompts: list[str] = field(default_factory=list)
    media_type: str = "image"
    created_at: str = ""
    updated_at: str = ""
