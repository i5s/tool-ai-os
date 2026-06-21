from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Model:
    id: str
    provider: str
    provider_model_id: str
    name: str
    description: str = ""
    version: str | None = None
    family: str | None = None
    media_types: list[str] = field(default_factory=lambda: ["image"])
    capabilities: dict = field(default_factory=dict)
    default_params: dict = field(default_factory=dict)
    status: str = "active"
    cost_per_unit: float | None = None
    cost_unit: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    registered_at: str = ""
    updated_at: str = ""
