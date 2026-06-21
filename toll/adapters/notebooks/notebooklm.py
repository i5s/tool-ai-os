from __future__ import annotations

import logging
from typing import Any

from ...core.connection_manager import ConnectionManager
from ...ports.notebook import NotebookPort, NotebookResponse

logger = logging.getLogger(__name__)


class NotebookLMProvider(NotebookPort):
    name = "notebooklm"

    def __init__(self, cm: ConnectionManager | None = None):
        self.cm = cm

    def is_available(self) -> bool:
        return False

    def is_strict_local(self) -> bool:
        return True

    async def upload_source(
        self, notebook_id: str, content: str, file_name: str, title: str = ""
    ) -> NotebookResponse:
        return NotebookResponse(
            success=False,
            error="not available: NotebookLM API not configured",
        )

    async def create_notes(
        self, notebook_id: str, source_ids: list[str] | None = None
    ) -> NotebookResponse:
        return NotebookResponse(
            success=False,
            error="not available: NotebookLM API not configured",
        )

    async def query(
        self, notebook_id: str, question: str
    ) -> NotebookResponse:
        return NotebookResponse(
            success=False,
            error="not available: NotebookLM API not configured",
        )

    async def list_sources(self, notebook_id: str) -> NotebookResponse:
        return NotebookResponse(
            success=False,
            error="not available: NotebookLM API not configured",
        )

    async def delete_source(
        self, notebook_id: str, source_id: str
    ) -> NotebookResponse:
        return NotebookResponse(
            success=False,
            error="not available: NotebookLM API not configured",
        )

    async def create_snapshot(
        self, notebook_id: str, label: str = ""
    ) -> NotebookResponse:
        return NotebookResponse(
            success=False,
            error="not available: NotebookLM API not configured",
        )

    async def list_snapshots(self, notebook_id: str) -> NotebookResponse:
        return NotebookResponse(
            success=False,
            error="not available: NotebookLM API not configured",
        )

    async def get_snapshot(
        self, notebook_id: str, snapshot_id: str
    ) -> NotebookResponse:
        return NotebookResponse(
            success=False,
            error="not available: NotebookLM API not configured",
        )

    async def delete_snapshot(
        self, notebook_id: str, snapshot_id: str
    ) -> NotebookResponse:
        return NotebookResponse(
            success=False,
            error="not available: NotebookLM API not configured",
        )

    async def generate_audio_overview(
        self, notebook_id: str, source_ids: list[str] | None = None
    ) -> NotebookResponse:
        return NotebookResponse(
            success=False,
            error="not available: NotebookLM API not configured",
        )


class NotebookLMResearchAdapter:
    def __init__(self, provider: NotebookLMProvider):
        self.provider = provider

    def to_research_source(self, source_data: dict) -> dict:
        return {
            "title": source_data.get("title", ""),
            "url": source_data.get("file_path", ""),
            "authors": [],
            "source_type": "notebook",
            "provider": "notebooklm",
            "relevance_score": 1.0,
            "confidence_score": 1.0,
            "citation": source_data.get("title", ""),
            "abstract": "",
        }

    def notebook_to_research_batch(
        self, sources: list[dict], notebook_title: str
    ) -> list[dict]:
        return [self.to_research_source(s) for s in sources]
