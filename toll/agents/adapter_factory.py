from __future__ import annotations

from typing import Any

from toll.agents.adapters.hermes import HermesAdapter
from toll.agents.adapters.opendesign import OpenDesignAdapter
from toll.adapters.llm.opencode import OpenCodeProvider


class AdapterFactory:
    @staticmethod
    def get_adapter(agent_name: str, **kwargs: Any):
        adapter_name = (agent_name or "").strip().lower()

        if adapter_name == "hermes":
            return HermesAdapter()

        if adapter_name in {"opencode", "open code"}:
            return OpenCodeProvider()

        if adapter_name in {"opendesign", "open design"}:
            return OpenDesignAdapter()

        raise ValueError(f"No adapter registered for agent: {agent_name!r}")
