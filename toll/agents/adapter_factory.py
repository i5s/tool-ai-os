from __future__ import annotations

from typing import Any

from .adapters import HermesAdapter
from ..adapters.llm.opencode import OpenCodeProvider


class AdapterFactory:
    @staticmethod
    def get_adapter(agent_name: str, **kwargs: Any):
        adapter_name = (agent_name or "").strip().lower()

        if adapter_name == "hermes":
            return HermesAdapter()

        if adapter_name in {"opencode", "open code"}:
            return OpenCodeProvider()

        raise ValueError(f"No adapter registered for agent: {agent_name!r}")
