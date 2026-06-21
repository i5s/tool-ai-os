from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from ..core.ai import AI
from ..core.connection_manager import ConnectionManager
from ..core.feature_flags import FeatureFlags
from ..engine.renderers.preview_renderer import PreviewRenderer
from ..model.artifact import Artifact, ArtifactStatus, ArtifactType
from ..ports.notebook import (
    Notebook,
    NotebookNote,
    NotebookPort,
    NotebookResponse,
    NotebookSnapshot,
    NotebookSource,
)
from .artifact_service import ArtifactService

logger = logging.getLogger(__name__)


class NotebookService:
    def __init__(
        self,
        artifact_service: ArtifactService,
        cm: ConnectionManager,
        flags: FeatureFlags | None = None,
        ai: AI | None = None,
        notebook_provider: NotebookPort | None = None,
    ):
        self.artifact_service = artifact_service
        self.cm = cm
        self.flags = flags or FeatureFlags(cm=cm)
        self.ai = ai or AI(cm=cm)
        self.notebook_provider = notebook_provider
        self.preview = PreviewRenderer()

    def create_notebook(
        self,
        title: str,
        description: str = "",
        workspace_type: str | None = None,
        workspace_id: str | None = None,
    ) -> Notebook:
        now = datetime.now(timezone.utc).isoformat()
        notebook = Notebook(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            workspace_type=workspace_type,
            workspace_id=workspace_id,
            created_at=now,
            updated_at=now,
        )
        self.cm.execute(
            """INSERT INTO notebooks (id, title, description, workspace_type, workspace_id,
               source_count, note_count, metadata, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 0, 0, '{}', ?, ?)""",
            (
                notebook.id,
                notebook.title,
                notebook.description,
                notebook.workspace_type,
                notebook.workspace_id,
                notebook.created_at,
                notebook.updated_at,
            ),
        )
        self.cm.commit()
        return notebook

    def list_notebooks(
        self,
        workspace_type: str | None = None,
        workspace_id: str | None = None,
    ) -> list[Notebook]:
        parts = ["SELECT * FROM notebooks WHERE 1=1"]
        params: list[Any] = []
        if workspace_type:
            parts.append("AND workspace_type = ?")
            params.append(workspace_type)
        if workspace_id:
            parts.append("AND workspace_id = ?")
            params.append(workspace_id)
        parts.append("ORDER BY updated_at DESC")
        rows = self.cm.connection.execute(" ".join(parts), params).fetchall()
        return [self._row_to_notebook(r) for r in rows]

    def get_notebook(self, notebook_id: str) -> Notebook | None:
        row = self.cm.connection.execute(
            "SELECT * FROM notebooks WHERE id = ?", (notebook_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_notebook(row)

    def update_notebook(self, notebook_id: str, title: str | None = None, description: str | None = None) -> Notebook | None:
        notebook = self.get_notebook(notebook_id)
        if not notebook:
            return None
        now = datetime.now(timezone.utc).isoformat()
        if title is not None:
            notebook.title = title
        if description is not None:
            notebook.description = description
        notebook.updated_at = now
        self.cm.execute(
            "UPDATE notebooks SET title=?, description=?, updated_at=? WHERE id=?",
            (notebook.title, notebook.description, notebook.updated_at, notebook.id),
        )
        self.cm.commit()
        return notebook

    def delete_notebook(self, notebook_id: str) -> bool:
        if self.flags.is_enabled("notebooklm_snapshots"):
            self._auto_snapshot(notebook_id, "before_delete")
        self.cm.execute("DELETE FROM notebooks WHERE id = ?", (notebook_id,))
        self.cm.commit()
        return True

    def upload_source(
        self, notebook_id: str, content: str, file_name: str, title: str = ""
    ) -> NotebookSource | None:
        notebook = self.get_notebook(notebook_id)
        if not notebook:
            return None
        strict = self.flags.is_enabled("notebooklm_strict_local")
        now = datetime.now(timezone.utc).isoformat()
        source = NotebookSource(
            id=str(uuid.uuid4()),
            notebook_id=notebook_id,
            title=title or file_name,
            file_name=file_name,
            char_count=len(content),
            created_at=now,
        )
        if not strict and self.notebook_provider:
            resp = self.notebook_provider.upload_source(
                notebook_id=notebook_id, content=content, file_name=file_name, title=title
            )
            if not resp.success:
                if resp.error and "not available" in (resp.error or ""):
                    logger.info("Provider unavailable, storing locally: %s", resp.error)
                else:
                    logger.warning("Provider upload failed: %s", resp.error)
        self.cm.execute(
            """INSERT INTO notebook_sources (id, notebook_id, title, file_name, file_path,
               content_type, char_count, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, 'text/plain', ?, '{}', ?)""",
            (source.id, source.notebook_id, source.title, source.file_name,
             source.file_path, source.char_count, source.created_at),
        )
        self.cm.execute(
            "UPDATE notebooks SET source_count = source_count + 1, updated_at = ? WHERE id = ?",
            (now, notebook_id),
        )
        self.cm.commit()
        return source

    def list_sources(self, notebook_id: str) -> list[NotebookSource]:
        rows = self.cm.connection.execute(
            "SELECT * FROM notebook_sources WHERE notebook_id = ? ORDER BY created_at DESC",
            (notebook_id,),
        ).fetchall()
        return [self._row_to_source(r) for r in rows]

    def delete_source(self, notebook_id: str, source_id: str) -> bool:
        if self.flags.is_enabled("notebooklm_snapshots"):
            self._auto_snapshot(notebook_id, f"before_delete_source_{source_id[:8]}")
        self.cm.execute(
            "DELETE FROM notebook_sources WHERE id = ? AND notebook_id = ?",
            (source_id, notebook_id),
        )
        self.cm.execute(
            "UPDATE notebooks SET source_count = MAX(0, source_count - 1), updated_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), notebook_id),
        )
        self.cm.commit()
        return True

    def create_notes(
        self, notebook_id: str, source_ids: list[str] | None = None
    ) -> list[NotebookNote]:
        notebook = self.get_notebook(notebook_id)
        if not notebook:
            return []
        sources = self.list_sources(notebook_id)
        if source_ids:
            sources = [s for s in sources if s.id in source_ids]
        if not sources:
            return []
        strict = self.flags.is_enabled("notebooklm_strict_local")
        notes: list[NotebookNote] = []
        now = datetime.now(timezone.utc).isoformat()
        for source in sources:
            content = self._generate_note_content(source, strict)
            note = NotebookNote(
                id=str(uuid.uuid4()),
                notebook_id=notebook_id,
                title=f"ملاحظة: {source.title}",
                content=content,
                source_ids=[source.id],
                created_at=now,
                updated_at=now,
            )
            self.cm.execute(
                """INSERT INTO notebook_notes (id, notebook_id, title, content, source_ids,
                   tags, metadata, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, '[]', '{}', ?, ?)""",
                (note.id, note.notebook_id, note.title, note.content,
                 json.dumps(note.source_ids, ensure_ascii=False),
                 note.created_at, note.updated_at),
            )
            notes.append(note)
        self.cm.execute(
            "UPDATE notebooks SET note_count = note_count + ?, updated_at = ? WHERE id = ?",
            (len(notes), now, notebook_id),
        )
        self.cm.commit()
        if self.flags.is_enabled("notebooklm_memory_index"):
            self._index_notes(notes)
        if self.flags.is_enabled("notebooklm_artifact_create"):
            self._create_artifact_from_notes(notebook, notes)
        return notes

    def query(self, notebook_id: str, question: str) -> str:
        notebook = self.get_notebook(notebook_id)
        if not notebook:
            return ""
        sources = self.list_sources(notebook_id)
        if not sources:
            return "لا توجد مصادر في هذا الدفتر."
        strict = self.flags.is_enabled("notebooklm_strict_local")
        source_text = "\n".join(
            f"[{i+1}] {s.title}: {self._get_source_content(s.id)}"
            for i, s in enumerate(sources[:10])
        )
        prompt = (
            f"أجب عن السؤال التالي بناءً على المصادر المتاحة في دفتر الملاحظات '{notebook.title}':\n\n"
            f"المصادر المتاحة ({len(sources)}):\n{source_text}\n\n"
            f"السؤال: {question}\n\n"
            f"قدم إجابة بالعربية بناءً على المصادر فقط. إذا لم تجد إجابة في المصادر، قل ذلك بوضوح."
        )
        if not strict and self.notebook_provider:
            resp = self.notebook_provider.query(notebook_id, question)
            if resp.success and resp.data:
                return str(resp.data)
        return self.ai.ask(prompt)

    def list_notes(self, notebook_id: str) -> list[NotebookNote]:
        rows = self.cm.connection.execute(
            "SELECT * FROM notebook_notes WHERE notebook_id = ? ORDER BY created_at DESC",
            (notebook_id,),
        ).fetchall()
        return [self._row_to_note(r) for r in rows]

    def delete_note(self, notebook_id: str, note_id: str) -> bool:
        self.cm.execute(
            "DELETE FROM notebook_notes WHERE id = ? AND notebook_id = ?",
            (note_id, notebook_id),
        )
        self.cm.execute(
            "UPDATE notebooks SET note_count = MAX(0, note_count - 1), updated_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), notebook_id),
        )
        self.cm.commit()
        return True

    def create_snapshot(self, notebook_id: str, label: str = "") -> NotebookSnapshot | None:
        if not self.flags.is_enabled("notebooklm_snapshots"):
            return None
        notebook = self.get_notebook(notebook_id)
        if not notebook:
            return None
        sources = self.list_sources(notebook_id)
        notes = self.list_notes(notebook_id)
        snapshot_data = {
            "notebook": {
                "id": notebook.id,
                "title": notebook.title,
                "description": notebook.description,
                "metadata": notebook.metadata,
            },
            "sources": [
                {
                    "id": s.id,
                    "title": s.title,
                    "file_name": s.file_name,
                    "char_count": s.char_count,
                }
                for s in sources
            ],
            "notes": [
                {
                    "id": n.id,
                    "title": n.title,
                    "content": n.content,
                    "source_ids": n.source_ids,
                    "tags": n.tags,
                }
                for n in notes
            ],
        }
        now = datetime.now(timezone.utc).isoformat()
        snapshot = NotebookSnapshot(
            id=str(uuid.uuid4()),
            notebook_id=notebook_id,
            label=label,
            snapshot_data=snapshot_data,
            source_count=len(sources),
            note_count=len(notes),
            created_at=now,
        )
        self.cm.execute(
            """INSERT INTO notebook_snapshots (id, notebook_id, label, snapshot_data,
               source_count, note_count, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (snapshot.id, snapshot.notebook_id, snapshot.label,
             json.dumps(snapshot.snapshot_data, ensure_ascii=False),
             snapshot.source_count, snapshot.note_count, snapshot.created_at),
        )
        self.cm.commit()
        if self.flags.is_enabled("notebooklm_artifact_create"):
            self._create_artifact_from_snapshot(notebook, snapshot)
        return snapshot

    def list_snapshots(self, notebook_id: str) -> list[NotebookSnapshot]:
        rows = self.cm.connection.execute(
            "SELECT * FROM notebook_snapshots WHERE notebook_id = ? ORDER BY created_at DESC",
            (notebook_id,),
        ).fetchall()
        return [self._row_to_snapshot(r) for r in rows]

    def get_snapshot(self, notebook_id: str, snapshot_id: str) -> NotebookSnapshot | None:
        row = self.cm.connection.execute(
            "SELECT * FROM notebook_snapshots WHERE id = ? AND notebook_id = ?",
            (snapshot_id, notebook_id),
        ).fetchone()
        if not row:
            return None
        return self._row_to_snapshot(row)

    def delete_snapshot(self, notebook_id: str, snapshot_id: str) -> bool:
        self.cm.execute(
            "DELETE FROM notebook_snapshots WHERE id = ? AND notebook_id = ?",
            (snapshot_id, notebook_id),
        )
        self.cm.commit()
        return True

    def generate_audio_overview(
        self, notebook_id: str, source_ids: list[str] | None = None
    ) -> dict:
        return {"error": "not implemented", "notebook_id": notebook_id}

    def _auto_snapshot(self, notebook_id: str, label: str):
        try:
            self.create_snapshot(notebook_id, label)
        except Exception as e:
            logger.warning("Auto-snapshot failed for %s: %s", notebook_id, e)

    def _generate_note_content(self, source: NotebookSource, strict: bool) -> str:
        content = self._get_source_content(source.id)
        if not content:
            return "لم يتم العثور على محتوى للمصدر."
        try:
            prompt = (
                f"لخص النص التالي بالعربية في فقرة واحدة مركزة:\n\n{content[:3000]}"
            )
            return self.ai.ask(prompt)
        except Exception as e:
            logger.warning("Note generation failed: %s", e)
            return content[:500]

    def _get_source_content(self, source_id: str) -> str:
        row = self.cm.connection.execute(
            "SELECT title, file_name, metadata FROM notebook_sources WHERE id = ?",
            (source_id,),
        ).fetchone()
        if not row:
            return ""
        return f"{row['title']} ({row['file_name']})"

    def _index_notes(self, notes: list[NotebookNote]):
        try:
            for note in notes:
                self.cm.execute(
                    "INSERT INTO notebook_notes_fts (title, content, tags) VALUES (?, ?, ?)",
                    (note.title, note.content, json.dumps(note.tags)),
                )
            self.cm.commit()
        except Exception as e:
            logger.warning("Memory indexing failed: %s", e)

    def _create_artifact_from_notes(self, notebook: Notebook, notes: list[NotebookNote]):
        try:
            artifact = Artifact(
                id="",
                type=ArtifactType.RESEARCH,
                status=ArtifactStatus.DRAFT,
                title=f"دفتر: {notebook.title}",
                content={
                    "notebook_id": notebook.id,
                    "note_count": len(notes),
                    "notes": [
                        {"title": n.title, "content": n.content, "source_ids": n.source_ids}
                        for n in notes
                    ],
                },
                intent="notebook_note",
                workspace_type=notebook.workspace_type,
                workspace_id=notebook.workspace_id,
            )
            rendered = self._render_artifact(notebook, notes)
            artifact = self.artifact_service.create(artifact, rendered)
            preview_html = self.preview.research_preview(artifact)
            preview_json = self.preview.json_preview(artifact)
            self.artifact_service.write_preview(artifact, preview_html, preview_json)
        except Exception as e:
            logger.warning("Artifact creation failed: %s", e)

    def _create_artifact_from_snapshot(self, notebook: Notebook, snapshot: NotebookSnapshot):
        try:
            artifact = Artifact(
                id="",
                type=ArtifactType.RESEARCH,
                status=ArtifactStatus.DRAFT,
                title=f"لقطة: {notebook.title} — {snapshot.label or 'غير معنون'}",
                content={
                    "notebook_id": notebook.id,
                    "snapshot_id": snapshot.id,
                    "label": snapshot.label,
                    "source_count": snapshot.source_count,
                    "note_count": snapshot.note_count,
                    "snapshot_data": snapshot.snapshot_data,
                },
                intent="notebook_snapshot",
                workspace_type=notebook.workspace_type,
                workspace_id=notebook.workspace_id,
            )
            rendered = self._render_snapshot(snapshot)
            artifact = self.artifact_service.create(artifact, rendered)
            preview_html = self.preview.research_preview(artifact)
            preview_json = self.preview.json_preview(artifact)
            self.artifact_service.write_preview(artifact, preview_html, preview_json)
        except Exception as e:
            logger.warning("Snapshot artifact creation failed: %s", e)

    def _render_artifact(self, notebook: Notebook, notes: list[NotebookNote]) -> str:
        note_list = "".join(
            f"""<div class="note-card">
              <h3>{n.title}</h3>
              <p>{n.content}</p>
            </div>"""
            for n in notes
        )
        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head><meta charset="UTF-8">
<title>{notebook.title} — ملاحظات</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:system-ui,serif; background:#f8f6f0; color:#1a1a2e; padding:40px; }}
.container {{ max-width:800px; margin:auto; background:#fff; padding:32px; border-radius:8px; }}
h1 {{ font-size:1.6rem; border-bottom:3px solid #0f3460; padding-bottom:8px; }}
.note-card {{ background:#f8fafc; padding:16px; border-radius:8px; margin:12px 0; }}
.note-card h3 {{ font-size:1.1rem; color:#0f3460; margin-bottom:6px; }}
</style>
</head>
<body>
<div class="container">
  <h1>{notebook.title}</h1>
  <p style="color:#64748b;margin:8px 0 16px;">{len(notes)} ملاحظة</p>
  {note_list}
</div>
</body>
</html>"""

    def _render_snapshot(self, snapshot: NotebookSnapshot) -> str:
        src_list = "".join(
            f"<li>{s['title']} ({s.get('file_name', '')})</li>"
            for s in snapshot.snapshot_data.get("sources", [])
        )
        note_list = "".join(
            f"""<div class="note-card">
              <h3>{n['title']}</h3>
              <p>{n['content']}</p>
            </div>"""
            for n in snapshot.snapshot_data.get("notes", [])
        )
        label = snapshot.label or "لقطة غير معنونة"
        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head><meta charset="UTF-8">
<title>لقطة — {label}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:system-ui,serif; background:#f8f6f0; color:#1a1a2e; padding:40px; }}
.container {{ max-width:800px; margin:auto; background:#fff; padding:32px; border-radius:8px; }}
h1 {{ font-size:1.6rem; border-bottom:3px solid #0f3460; padding-bottom:8px; }}
.meta {{ color:#64748b; font-size:.9rem; margin:8px 0 16px; }}
.note-card {{ background:#f8fafc; padding:16px; border-radius:8px; margin:12px 0; }}
.note-card h3 {{ font-size:1.1rem; color:#0f3460; margin-bottom:6px; }}
</style>
</head>
<body>
<div class="container">
  <h1>{label}</h1>
  <div class="meta">{snapshot.source_count} مصادر • {snapshot.note_count} ملاحظات</div>
  <h2>المصادر</h2>
  <ul>{src_list}</ul>
  <h2>الملاحظات</h2>
  {note_list}
</div>
</body>
</html>"""

    def _row_to_notebook(self, row) -> Notebook:
        return Notebook(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            workspace_type=row["workspace_type"],
            workspace_id=row["workspace_id"],
            source_count=row["source_count"],
            note_count=row["note_count"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_source(self, row) -> NotebookSource:
        return NotebookSource(
            id=row["id"],
            notebook_id=row["notebook_id"],
            title=row["title"],
            file_name=row["file_name"],
            file_path=row["file_path"],
            content_type=row["content_type"],
            char_count=row["char_count"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=row["created_at"],
        )

    def _row_to_note(self, row) -> NotebookNote:
        return NotebookNote(
            id=row["id"],
            notebook_id=row["notebook_id"],
            title=row["title"],
            content=row["content"],
            source_ids=json.loads(row["source_ids"]) if row["source_ids"] else [],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_snapshot(self, row) -> NotebookSnapshot:
        return NotebookSnapshot(
            id=row["id"],
            notebook_id=row["notebook_id"],
            label=row["label"],
            snapshot_data=json.loads(row["snapshot_data"]) if row["snapshot_data"] else {},
            source_count=row["source_count"],
            note_count=row["note_count"],
            created_at=row["created_at"],
        )
