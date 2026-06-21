from __future__ import annotations

from dataclasses import dataclass

from ..model.artifact import ArtifactType
from .registry import ProviderRegistry
from .settings import Settings
from .feature_flags import FeatureFlags


@dataclass
class ProviderCandidate:
    provider_name: str
    quality_score: float
    available: bool
    preferred_by_user: bool
    allowed_by_flag: bool


class ProviderSelector:
    def __init__(self, registry: ProviderRegistry, settings: Settings, flags: FeatureFlags):
        self.registry = registry
        self.settings = settings
        self.flags = flags

    def select(self, task_type: ArtifactType, prefer: str | None = None) -> str | None:
        available = self.registry.available_llm()
        user_pref = prefer or self.settings.get(f"provider_for_{task_type.value}")

        candidates: list[ProviderCandidate] = []
        for name in available:
            candidates.append(ProviderCandidate(
                provider_name=name,
                quality_score=self._quality_score(name),
                available=True,
                preferred_by_user=(name == user_pref) if user_pref else False,
                allowed_by_flag=self.flags.is_enabled(f"provider_{name}", default=True),
            ))

        if not candidates:
            return None

        def score(c: ProviderCandidate) -> float:
            s = 0.0
            if c.allowed_by_flag:
                s += 10.0
            if c.preferred_by_user:
                s += 20.0
            s += c.quality_score * 5.0
            return s

        candidates.sort(key=score, reverse=True)
        for c in candidates:
            if c.allowed_by_flag:
                return c.provider_name
        return candidates[0].provider_name

    def _quality_score(self, provider: str) -> float:
        scores: dict[str, float] = {
            "opencode": 0.9,
            "ollama": 0.5,
        }
        return scores.get(provider, 0.3)
