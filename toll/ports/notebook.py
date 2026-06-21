from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class NotebookSource:
    id: str
    notebook_id: str
    title: str
    file_name: str
    content: str = ""
    file_path: str | None = None
    content_type: str = "text/plain"
    char_count: int = 0
    metadata: dict = field(default_factory=dict)
    created_at: str = ""


@dataclass
class NotebookNote:
    id: str
    notebook_id: str
    title: str
    content: str
    source_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""


@dataclass
class NotebookSnapshot:
    id: str
    notebook_id: str
    label: str
    snapshot_data: dict = field(default_factory=dict)
    source_count: int = 0
    note_count: int = 0
    created_at: str = ""


@dataclass
class Notebook:
    id: str
    title: str
    description: str = ""
    workspace_type: str | None = None
    workspace_id: str | None = None
    source_count: int = 0
    note_count: int = 0
    metadata: dict = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""


@dataclass
class NotebookResponse:
    success: bool
    data: Any = None
    error: str | None = None


class NotebookPort(ABC):
    name: str = "abstract_notebook"

    @abstractmethod
    def upload_source(
        self, notebook_id: str, content: str, file_name: str, title: str = ""
    ) -> NotebookResponse:
        ...

    @abstractmethod
    def create_notes(
        self, notebook_id: str, source_ids: list[str] | None = None
    ) -> NotebookResponse:
        ...

    @abstractmethod
    def query(
        self, notebook_id: str, question: str
    ) -> NotebookResponse:
        ...

    @abstractmethod
    def list_sources(
        self, notebook_id: str
    ) -> NotebookResponse:
        ...

    @abstractmethod
    def delete_source(
        self, notebook_id: str, source_id: str
    ) -> NotebookResponse:
        ...

    @abstractmethod
    def create_snapshot(
        self, notebook_id: str, label: str = ""
    ) -> NotebookResponse:
        ...

    @abstractmethod
    def list_snapshots(
        self, notebook_id: str
    ) -> NotebookResponse:
        ...

    @abstractmethod
    def get_snapshot(
        self, notebook_id: str, snapshot_id: str
    ) -> NotebookResponse:
        ...

    @abstractmethod
    def delete_snapshot(
        self, notebook_id: str, snapshot_id: str
    ) -> NotebookResponse:
        ...

    @abstractmethod
    def generate_audio_overview(
        self, notebook_id: str, source_ids: list[str] | None = None
    ) -> NotebookResponse:
        ...

    def is_available(self) -> bool:
        return True

    def is_strict_local(self) -> bool:
        return False
