"""Context Engine.

Builds a summarized context window for the LLM by combining:
- Active workspace state
- Relevant memories from Memory Graph
- Recent conversation history

Returns a prompt-ready context string plus structured metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core.connection_manager import ConnectionManager
from ..memory.graph import MemoryGraph
from ..workspace.manager import WorkspaceManager


@dataclass
class ContextResult:
    prompt: str
    memories: list[dict]
    active_workspace: dict
    recent_messages: list[dict]


class ContextEngine:
    def __init__(
        self,
        cm: ConnectionManager,
        memory_graph: MemoryGraph | None = None,
        workspace_manager: WorkspaceManager | None = None,
    ):
        self.cm = cm
        self.memory = memory_graph or MemoryGraph(cm=cm)
        self.workspace = workspace_manager or WorkspaceManager(cm=cm)

    def build(
        self,
        message: str,
        recent_messages: list[dict] | None = None,
        memory_limit: int = 10,
        message_history_limit: int = 6,
    ) -> ContextResult:
        active = self.workspace.get_active()
        summary = self.workspace.get_active_summary()

        memories = self.memory.retrieve(
            brand_id=active.active_brand_id,
            university_id=active.active_university_id,
            project_id=active.active_project_id,
            limit=memory_limit,
        )

        recent = (recent_messages or [])[-message_history_limit:]

        prompt = self._format_prompt(message, summary, memories, recent)

        return ContextResult(
            prompt=prompt,
            memories=[m.to_dict() for m in memories],
            active_workspace=summary,
            recent_messages=recent,
        )

    def _format_prompt(
        self,
        message: str,
        workspace_summary: dict,
        memories: list,
        recent_messages: list[dict],
    ) -> str:
        parts: list[str] = []

        ws_parts = []
        for key in ["brand", "university", "project", "semester"]:
            item = workspace_summary.get(key)
            if item:
                ws_parts.append(f"{key}: {item['name']}")
        if ws_parts:
            parts.append("[Workspace Context]\n" + "\n".join(ws_parts))

        if memories:
            parts.append("[Relevant Memories]")
            for m in memories:
                entity = f" ({m.entity_id})" if m.entity_id else ""
                parts.append(
                    f"- [{m.type}{entity}] {m.key}: {m.value} "
                    f"(importance: {m.importance_score})"
                )

        if recent_messages:
            parts.append("[Recent Conversation]")
            for msg in recent_messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "assistant" and len(content) > 300:
                    content = content[:300] + "..."
                parts.append(f"{role}: {content}")

        parts.append(f"[Current Message]\n{message}")

        return "\n\n".join(parts)
