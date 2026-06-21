# Sprint 5B: NotebookLM Integration — Design Review

## 1. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────────┐ │
│  │  Notebook   │ │  Research    │ │  Workflow        │ │
│  │  Service    │ │  Service     │ │  Engine          │ │
│  └──────┬──────┘ └──────┬───────┘ └────────┬─────────┘ │
└─────────┼───────────────┼──────────────────┼────────────┘
          │               │                  │
┌─────────┼───────────────┼──────────────────┼────────────┐
│         ▼               ▼                  ▼            │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Domain / Port Layer                  │   │
│  │  ┌────────────┐  ┌──────────────┐  ┌──────────┐  │   │
│  │  │ResearchSource│ │NotebookPort  │  │ResearchQ.│  │   │
│  │  └────────────┘  └──────┬───────┘  └──────────┘  │   │
│  └─────────────────────────┼─────────────────────────┘   │
│                            │                             │
│  ┌─────────────────────────┼─────────────────────────┐   │
│  │           Adapter Layer ▼                          │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────┐   │   │
│  │  │ NotebookLM   │ │ WebResearcher│ │ FutureN  │   │   │
│  │  │ Provider     │ │ (existing)   │ │ Provider │   │   │
│  │  └──────────────┘ └──────────────┘ └──────────┘   │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │              Infrastructure Layer                   │   │
│  │  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌────────┐  │   │
│  │  │ SQLite   │ │  File    │ │Memory  │ │Feature │  │   │
│  │  │ (local)  │ │ System   │ │ Graph  │ │ Flags  │  │   │
│  │  └──────────┘ └──────────┘ └────────┘ └────────┘  │   │
│  └────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Role |
|-------|------|
| **Application** | Orchestration: `NotebookService` owns notebook CRUD + sync; `ResearchService` delegates to providers via port |
| **Port** | `NotebookPort` defines the notebook-provider contract; `ResearchSource` is reused as the source data shape |
| **Adapter** | `NotebookLMProvider` implements `NotebookPort`; may wrap HTTP, headless browser, or SDK |
| **Infrastructure** | SQLite stores notebooks/sources/notes; File System stores uploaded source blobs; Memory Graph indexes note content |

### Key Design Decisions

1. **New port, not overloaded**: `NotebookPort` is separate from `ResearchSource` because notebook workflows are fundamentally different from search—they involve uploading sources, managing notebooks, and querying within a bounded context.
2. **`ResearchSource` is reused for result shape**: When NotebookLM produces notes/sources, they are normalized into `ResearchSource` objects to unify downstream processing (citation, memory storage, artifact rendering).
3. **No new engine**: Notebook operations use the existing `WorkflowEngine` with `notebook_*` handler types; no sub-engine needed.

---

## 2. Data Flow

### 2.1 Source Upload Flow

```
User Uploads File
       │
       ▼
┌──────────────────┐
│  Frontend POST   │  /api/notebooks/{id}/sources
│  multipart/form  │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────┐
│  NotebookService.upload()    │
│  1. Save to local filesystem │
│     data/notebooks/{id}/     │
│  2. Store metadata in SQLite │
│     notebook_sources table   │
│  3. Sync to NotebookLM via   │
│     NotebookPort.upload()    │
│  4. Mark source as SYNCED    │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  NotebookLMProvider.upload() │
│  1. Authenticate session     │
│  2. Upload source blob       │
│  3. Return remote_source_id  │
│  4. Store in provider_meta   │
└──────────────────────────────┘
```

### 2.2 Query / Chat Flow

```
User Sends Message
       │
       ▼
┌──────────────────┐
│  POST /api/chat  │  (existing endpoint)
│  with notebook   │
│  context flag    │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────┐
│  NotebookService.query()     │
│  1. Check local note cache   │
│     (SQLite, full-text)      │
│  2. If cache miss:           │
│     NotebookPort.query()     │
│  3. Store result as note     │
│     in notebook_notes        │
│  4. Index into MemoryGraph   │
│     (entity→note summary)    │
│  5. Return response          │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  Response returned to chat   │
│  with optional artifact      │
│  reference                   │
└──────────────────────────────┘
```

### 2.3 Sync Flow (background)

```
Trigger: periodic / user-initiated
       │
       ▼
┌──────────────────────────────┐
│  NotebookService.sync()      │
│  1. List sources with        │
│     status != SYNCED         │
│  2. Upload each via port     │
│  3. Update status → SYNCED   │
│  4. Pull new notes from      │
│     NotebookLM (delta)       │
│  5. Store new notes locally  │
│  6. Index into MemoryGraph   │
│  7. Create Artifact if       │
│     notes changed            │
└──────────────────────────────┘
```

---

## 3. Provider Design

### 3.1 Port Interface

```python
# toll/ports/notebook.py

class NotebookPort(ABC):
    """Port for notebook providers (NotebookLM, etc.)."""

    @abstractmethod
    def upload_source(
        self,
        notebook_id: str,
        file_path: Path,
        source_type: str,       # "pdf", "url", "text", "audio"
        title: str | None = None,
    ) -> dict:
        """Upload a source to the remote notebook.
        Returns remote metadata dict (id, status, etc.).
        """
        ...

    @abstractmethod
    def query(
        self,
        notebook_id: str,
        message: str,
        source_ids: list[str] | None = None,
    ) -> NotebookResponse:
        """Query the notebook. Optionally constrain to sources."""
        ...

    @abstractmethod
    def list_sources(
        self,
        notebook_id: str,
    ) -> list[dict]:
        """List all sources in a remote notebook."""
        ...

    @abstractmethod
    def delete_source(
        self,
        notebook_id: str,
        remote_source_id: str,
    ) -> bool:
        """Delete a source from the remote notebook."""
        ...

    @abstractmethod
    def health(self) -> bool:
        """Is the provider reachable/configured?"""
        ...


@dataclass
class NotebookResponse:
    text: str
    sources_used: list[str]       # source_ids referenced
    provider: str
    confidence: float = 1.0
```

### 3.2 NotebookLM Adapter Implementation Sketch

```python
# toll/adapters/notebooks/notebooklm.py

class NotebookLMProvider(NotebookPort):
    """Adapter for Google NotebookLM.

    Strategy: TBD — may use:
      A) Headless browser automation (Playwright) if no public API
      B) 3rd-party reverse-engineered SDK
      C) Official API if/when released

    All strategies share the same Port contract.
    """

    def __init__(self, config: dict):
        self.session_id = config.get("session_id")
        self.base_url = config.get("base_url", "https://notebooklm.google.com")
        self._client = None

    def upload_source(self, notebook_id, file_path, source_type, title=None):
        # Implementation detail hidden behind port
        ...

    def query(self, notebook_id, message, source_ids=None):
        # Implementation detail hidden behind port
        ...

    def health(self) -> bool:
        return self.session_id is not None
```

### 3.3 Provider Selection

The existing `ProviderSelector` (`toll/core/provider_selector.py`) already handles multi-provider selection with fallback. It will be extended to include notebook provider selection:

```python
# In ProviderSelector:
NOTEBOOK_CAPABILITY = "notebook"

def select_notebook(self) -> str | None:
    """Select a provider for notebook operations."""
    return self._select_with_capability(self.NOTEBOOK_CAPABILITY)
```

Providers register their capabilities:

```python
# ProviderRegistry registration:
registry.register("notebooklm", NotebookLMProvider, capabilities=["notebook"])
```

---

## 4. Feature Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `notebooklm_enabled` | `false` | Master toggle for NotebookLM integration |
| `notebooklm_auto_sync` | `true` | Auto-sync sources on upload |
| `notebooklm_memory_index` | `true` | Index notebook notes into MemoryGraph |
| `notebooklm_artifact_create` | `true` | Create Artifacts from notebook sessions |
| `notebooklm_max_sources` | `50` | Max sources per notebook (config via settings) |
| `notebooklm_strict_local` | `false` | When true: no source uploads leave the local machine, no NotebookLM calls, notebook features fall back to local storage only |
| `notebooklm_snapshots` | `true` | Enable notebook snapshot/checkpoint creation |
| `notebooklm_audio_overview` | `false` | Enable NotebookLM Audio Overview generation |

All flags defined in `toll/core/feature_flags.py` with the same pattern:
```python
NOTEBOOK_FLAGS: dict[str, bool] = {
    "notebooklm_enabled": False,
    "notebooklm_auto_sync": True,
    "notebooklm_memory_index": True,
    "notebooklm_artifact_create": True,
    "notebooklm_strict_local": False,
    "notebooklm_snapshots": True,
    "notebooklm_audio_overview": False,
}
```

---

## 5. Storage Impact

### 5.1 New Tables (Migration 0006)

```sql
-- notebooks table
CREATE TABLE notebooks (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    provider TEXT NOT NULL,           -- "notebooklm"
    provider_notebook_id TEXT,        -- remote notebook ID
    provider_meta TEXT DEFAULT '{}',  -- JSON blob for provider state
    sources_count INTEGER DEFAULT 0,
    notes_count INTEGER DEFAULT 0,
    last_synced_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (workspace_id) REFERENCES workspace_state(workspace_id)
);

-- notebook_sources table
CREATE TABLE notebook_sources (
    id TEXT PRIMARY KEY,
    notebook_id TEXT NOT NULL,
    source_type TEXT NOT NULL,        -- "pdf", "url", "text", "audio"
    title TEXT,
    source_uri TEXT NOT NULL,         -- local path or URL
    content_hash TEXT,                -- SHA256 of local copy
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, uploading, synced, failed
    provider_source_id TEXT,          -- remote source ID
    error_message TEXT,
    file_size INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
);

-- notebook_notes table (full-text indexed)
CREATE TABLE notebook_notes (
    id TEXT PRIMARY KEY,
    notebook_id TEXT NOT NULL,
    query_text TEXT NOT NULL,
    response_text TEXT NOT NULL,
    source_ids TEXT DEFAULT '[]',     -- JSON array of notebook_source IDs
    provider TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
);

CREATE VIRTUAL TABLE notebook_notes_fts USING fts5(
    query_text, response_text,
    content='notebook_notes',
    content_rowid='rowid'
);
```

### 5.2 File Storage

```
data/
├── notebooks/
│   ├── {notebook_id}/
│   │   ├── sources/
│   │   │   ├── {source_id}.pdf       # original uploaded file
│   │   │   └── {source_id}.meta.json # extracted metadata
│   │   └── exports/
│   │       └── {timestamp}_export.pdf # notebook export
│   └── archive/                       # deleted notebook files
└── artifacts/
    └── ...                            # existing artifact storage
```

### 5.3 Migration 0006 Checklist

- Create all 3 tables + FTS index
- Add indexes: `notebooks(workspace_id)`, `notebook_sources(notebook_id)`, `notebook_notes(notebook_id)`
- Ensure cascade deletes work for workspace deletion
- No existing data migration needed (new feature)

---

## 6. API Design

### 6.1 New Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/notebooks` | List notebooks (filter by workspace) |
| `POST` | `/api/notebooks` | Create notebook |
| `GET` | `/api/notebooks/{id}` | Get notebook details |
| `PUT` | `/api/notebooks/{id}` | Update notebook (title, description) |
| `DELETE` | `/api/notebooks/{id}` | Delete notebook + cascade sources |
| `POST` | `/api/notebooks/{id}/sync` | Trigger sync |
| `GET` | `/api/notebooks/{id}/sources` | List notebook sources |
| `POST` | `/api/notebooks/{id}/sources` | Upload a source (multipart) |
| `DELETE` | `/api/notebooks/{id}/sources/{sid}` | Delete a source |
| `POST` | `/api/notebooks/{id}/query` | Query the notebook |
| `GET` | `/api/notebooks/{id}/notes` | List notes |

### 6.2 Request/Response Shapes

```python
# toll/ports/notebook.py (API models section)

class NotebookCreate(BaseModel):
    title: str
    description: str = ""
    workspace_id: str

class NotebookUpdate(BaseModel):
    title: str | None = None
    description: str | None = None

class SourceUploadResponse(BaseModel):
    source_id: str
    status: str
    file_size: int
    provider_source_id: str | None = None

class NotebookQuery(BaseModel):
    message: str
    source_ids: list[str] | None = None

class NotebookQueryResponse(BaseModel):
    text: str
    sources_used: list[str]
    notes: list[dict]      # stored notes references
    artifact_id: str | None = None  # if artifact was created
```

### 6.3 Existing Endpoint Changes

- `POST /api/chat`: New optional field `notebook_id` — when set, the chat flow queries the notebook context before generating the response.
- `POST /api/chat`: Response extended with optional `notebook_sources` and `notebook_notes` fields.

---

## 7. UI Design

### 7.1 New Sidebar Section

```
┌──────────────────────┐
│  📓 Notebooks        │  ← collapsible section
│                      │
│  ┌────────────────┐  │
│  │ 🔍 بحث...      │  │  ← filter notebooks
│  └────────────────┘  │
│                      │
│  📘 Research Paper   │  ← notebook item
│     12 sources       │     source/note counts
│     45 notes         │
│  📗 Product Docs     │
│     3 sources        │
│     8 notes          │
│                      │
│  [+ New Notebook]    │  ← create action
└──────────────────────┘
```

### 7.2 Notebook Detail View

```
┌──────────────────────────────────────┐
│  ← Back to Notebooks                 │
│                                      │
│  📘 Research Paper                   │
│  ┌────────────┐  ┌──────────────────┐│
│  │ 📄 Sources  │  │ 💬 Chat with     ││
│  │            │  │    Notebook      ││
│  │ [Upload]   │  │                  ││
│  │ [Add URL]  │  │ ┌──────────────┐ ││
│  │            │  │ │ What were the │ ││
│  │ • paper1   │  │ │ key findings? │ ││
│  │ • paper2   │  │ └──────────────┘ ││
│  │ • url:...  │  │                  ││
│  │            │  │ ┌──────────────┐ ││
│  │            │  │ │ The key      │ ││
│  │            │  │ │ findings are  │ ││
│  │            │  │ │ ...          │ ││
│  │            │  │ └──────────────┘ ││
│  │            │  │                  ││
│  │            │  │ [📝 Save Note]  │ ││
│  └────────────┘  └──────────────────┘│
└──────────────────────────────────────┘
```

### 7.3 File Upload UX

```javascript
// No new UI framework — extend existing web/index.html patterns:
// 1. Drag-and-drop zone in Sources panel
// 2. File picker via <input type="file">
// 3. Upload progress bar (XMLHttpRequest.upload.onprogress)
// 4. Status badge per source: pending → uploading → synced → failed
```

### 7.4 Messages Integration

When a chat message references notebook context, the response will include a subtle NotebookLM citation badge:

```
Assistant: Based on your research notebook, the key findings are...

[📓 Research Paper · 3 sources]     ← clickable badge
```

---

## 8. Workflow Integration

### 8.1 New Handler Types

```python
# Registered in handler_registry.py with notebooklm_enabled flag:

if flags.is_enabled("notebooklm_enabled"):
    svc = NotebookService(artifact_service, selector, cm, flags)
    wf_engine.register_handler("notebook_create", svc.create_workflow)
    wf_engine.register_handler("notebook_query", svc.query_workflow)
    wf_engine.register_handler("notebook_upload", svc.upload_workflow)
    wf_engine.register_handler("notebook_sync", svc.sync_workflow)
```

### 8.2 Workflow Examples

```python
# Plan → Workflow mapping:
plan = {
    "intent": "notebook_create",
    "title": "Q1 Market Research",
    "workspace_id": "uni_123",
    "description": "Competitor analysis sources"
}
# → WorkflowEngine routes to NotebookService.create_workflow()
# → Approvals: CREATE = auto_execute, UPLOAD = auto, QUERY = auto

plan = {
    "intent": "notebook_query",
    "notebook_id": "nb_456",
    "message": "Summarize key competitors"
}
# → WorkflowEngine routes to NotebookService.query_workflow()
# → Returns NotebookQueryResponse
```

### 8.3 Approval Levels

| Intent | Level | Rationale |
|--------|-------|-----------|
| `notebook_create` | AUTO | Creating a notebook container is low-risk |
| `notebook_upload` | AUTO | Uploading sources is local-first; sync is background |
| `notebook_query` | AUTO | Read-only operation |
| `notebook_sync` | AUTO | Background data reconciliation |
| `notebook_delete` | APPROVAL | Destructive operation with cascade |

---

## 9. Artifact Integration

### 9.1 Artifact Creation Strategy

Notebook notes become Artifacts following the same pattern as research reports:

```python
# In NotebookService:

def _notes_to_artifact(self, notebook_id: str, query: str, response: NotebookResponse) -> Artifact:
    artifact = Artifact(
        id="",
        type=ArtifactType.RESEARCH,  # Reuse RESEARCH type (notes are research artifacts)
        status=ArtifactStatus.COMPLETED,
        title=f"Notebook Note: {query[:60]}",
        content={
            "notebook_id": notebook_id,
            "query": query,
            "response": response.text,
            "sources_used": response.sources_used,
            "provider": response.provider,
        },
        intent="notebook_note",
        workspace_type="notebook",
        workspace_id=notebook_id,
        tags=["notebook", "note", response.provider],
    )
    return self.artifact_service.create(artifact)
```

### 9.2 Artifact Type Consideration

| Option | Pros | Cons |
|--------|------|------|
| Reuse `ArtifactType.RESEARCH` | No new enum value; works with existing renderers | Loses notebook-specific identity |
| New `ArtifactType.NOTEBOOK_NOTE` | Explicit; filterable | New enum; new renderer needed |
| **Recommendation** | Reuse `RESEARCH` with `intent="notebook_note"` for now. Add `NOTEBOOK_NOTE` enum in a later sprint if filtering proves necessary. |

### 9.3 Versioning

Each query to the same notebook produces a new artifact (version chain via `parent_artifact_id`). Subsequent queries to the same notebook with the same question update the existing artifact rather than creating a new one (idempotent by notebook_id + query hash).

---

## 10. Research Integration

### 10.1 NotebookLM as ResearchProvider

NotebookLM implements the existing `ResearchSource` port but adds notebook-specific semantics:

```python
# toll/adapters/notebooks/notebooklm.py (partial)

class NotebookLMResearchAdapter(ResearchSource):
    """Wraps NotebookLM as a generic ResearchSource for unified search flow."""

    def __init__(self, notebook_service: NotebookService, notebook_id: str):
        self.notebook_service = notebook_service
        self.notebook_id = notebook_id

    async def search(self, query: ResearchQuery) -> list[ResearchSource]:
        """Search within the notebook's sources."""
        response = self.notebook_service.query(
            notebook_id=self.notebook_id,
            message=query.query,
        )
        # Parse response into ResearchSource objects
        return [ResearchSource(
            title=f"NotebookLM: {query.query[:50]}",
            url=None,
            authors=[],
            year=None,
            source_type="notebook_note",
            abstract=response.text,
            provider="notebooklm",
        )]
```

### 10.2 Memory Graph Integration

```python
# In NotebookService.query():
notes_response = provider.query(notebook_id, message)
if flags.is_enabled("notebooklm_memory_index"):
    self._index_into_memory(notebook_id, message, notes_response.text)

def _index_into_memory(self, notebook_id: str, query: str, response: str):
    """Store notebook note summaries into MemoryGraph."""
    memory = self.memory_graph.store(
        agent_id="notebooklm",
        entity_id=notebook_id,
        entity_type="notebook",
        key=f"note:{hash(query)}",
        value={
            "query": query[:200],
            "summary": response[:500],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
```

### 10.3 Source Reuse

When the `ResearchService.execute()` runs, it can optionally include notebook sources:

```python
# In ResearchService:
if flags.is_enabled("notebooklm_enabled"):
    for nb in self.notebook_service.list(workspace_id):
        adapter = NotebookLMResearchAdapter(self.notebook_service, nb["id"])
        providers.append(adapter)
```

This means a research query can automatically search all notebooks in the current workspace alongside web sources.

---

## 11. Notebook Snapshot Support

### 11.1 Purpose

A snapshot is a point-in-time capture of a notebook's full state — all sources, all notes, and the notebook metadata. Snapshots serve as:
- **Checkpoints**: Before destructive operations (mass delete, re-sync), auto-snapshot for rollback
- **Comparison**: Diff two snapshots to see what changed between queries
- **Export material**: A snapshot is the atomic unit for notebook export (PDF, Markdown, zip)
- **Artifact source**: Each snapshot creates an Artifact, making notebook state visible in the artifact system

### 11.2 Storage Model

```sql
-- notebook_snapshots table
CREATE TABLE notebook_snapshots (
    id TEXT PRIMARY KEY,
    notebook_id TEXT NOT NULL,
    label TEXT,                            -- user-provided label or auto-generated
    reason TEXT DEFAULT 'manual',          -- "manual", "pre_delete", "pre_sync", "auto"
    source_count INTEGER DEFAULT 0,
    note_count INTEGER DEFAULT 0,
    total_size_bytes INTEGER DEFAULT 0,
    snapshot_data TEXT NOT NULL,            -- JSON: full state dump of sources + notes
    artifact_id TEXT,                      -- link to created Artifact (if not null)
    created_at TEXT NOT NULL,
    FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
);
```

`sources_count` and `notes_count` on the `notebooks` table are incremented/decremented by triggers on `notebook_sources` and `notebook_notes`.

### 11.3 Snapshot Contents

The `snapshot_data` JSON blob captures:

```json
{
  "notebook": {
    "id": "nb_123",
    "title": "Research Paper",
    "description": "...",
    "provider": "notebooklm"
  },
  "sources": [
    {
      "id": "src_1",
      "source_type": "pdf",
      "title": "paper.pdf",
      "source_uri": "/path/to/file",
      "content_hash": "sha256:...",
      "status": "synced"
    }
  ],
  "notes": [
    {
      "id": "note_1",
      "query_text": "summarize findings",
      "response_text": "The key findings are...",
      "source_ids": ["src_1"],
      "created_at": "2026-06-21T..."
    }
  ],
  "created_at": "2026-06-21T..."
}
```

### 11.4 Snapshot Lifecycle

```
Create Snapshot (user or auto)
       │
       ▼
┌──────────────────────────────────┐
│ NotebookService.create_snapshot() │
│ 1. Lock notebook (prevent writes) │
│ 2. Read all sources + notes      │
│ 3. Serialize to snapshot_data    │
│ 4. INSERT into notebook_snapshots│
│ 5. Create Artifact from snapshot │
│    (ArtifactType.RESEARCH,       │
│     intent="notebook_snapshot")  │
│ 6. Release lock                  │
│ 7. Return snapshot + artifact_id │
└──────────────────────────────────┘
```

### 11.5 API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/notebooks/{id}/snapshots` | Create snapshot (optional `label`) |
| `GET` | `/api/notebooks/{id}/snapshots` | List snapshots |
| `GET` | `/api/notebooks/{id}/snapshots/{sid}` | Get snapshot detail |
| `DELETE` | `/api/notebooks/{id}/snapshots/{sid}` | Delete snapshot |

### 11.6 Auto-Snapshot Triggers

Triggered automatically when `notebooklm_snapshots` is enabled:

| Trigger | Reason | Behavior |
|---------|--------|----------|
| Before source delete | `pre_delete` | Snapshot then delete |
| Before sync | `pre_sync` | Snapshot then sync |
| Before notebook delete | `pre_notebook_delete` | Snapshot then cascade delete |
| Periodic (every N queries) | `auto` | Every 10th query auto-snapshots |

### 11.7 Snapshot → Artifact Mapping

```python
def _snapshot_to_artifact(self, snapshot: dict) -> Artifact:
    artifact = Artifact(
        id="",
        type=ArtifactType.RESEARCH,
        status=ArtifactStatus.COMPLETED,
        title=f"Notebook Snapshot: {snapshot['label'] or snapshot['id']}",
        content={
            "snapshot_id": snapshot["id"],
            "notebook_id": snapshot["notebook_id"],
            "reason": snapshot["reason"],
            "source_count": snapshot["source_count"],
            "note_count": snapshot["note_count"],
            "total_size_bytes": snapshot["total_size_bytes"],
        },
        intent="notebook_snapshot",
        tags=["notebook", "snapshot"],
    )
    return self.artifact_service.create(artifact)
```

---

## 12. Implementation Plan

### Phase 1: Foundation (files 1–4)

| Step | File | What |
|------|------|------|
| 1.1 | `toll/ports/notebook.py` | Define `NotebookPort`, `NotebookResponse`, API model classes |
| 1.2 | `toll/core/feature_flags.py` | Register `NOTEBOOK_FLAGS` dict; load during `_ensure_defaults` |
| 1.3 | `toll/model/migrations/0006_notebooks.sql` | All 4 tables (notebooks, sources, notes, snapshots) + FTS + indexes |
| 1.4 | `toll/model/migrations/__init__.py` | No change needed; runner auto-discovers `.sql` files |

**Gate:** Migration 0006 applies cleanly; feature flags visible in `GET /api/config`.

### Phase 2: Service Layer (files 5–7)

| Step | File | What |
|------|------|------|
| 2.1 | `toll/application/notebook_service.py` | `NotebookService` with CRUD + upload + query + sync + snapshot |
| 2.2 | `toll/application/handler_registry.py` | Register `notebook_*` handlers behind `notebooklm_enabled` flag |
| 2.3 | `toll/core/provider_selector.py` | Add `NOTEBOOK_CAPABILITY` + `select_notebook()` method |

**Gate:** `NotebookService` unit tests pass; handlers registered in `WorkflowEngine`.

### Phase 3: Provider Layer (files 8–9)

| Step | File | What |
|------|------|------|
| 3.1 | `toll/adapters/notebooks/__init__.py` | Package init |
| 3.2 | `toll/adapters/notebooks/notebooklm.py` | `NotebookLMProvider(NotebookPort)` + `NotebookLMResearchAdapter` |

**Gate:** `NotebookLMProvider.health()` returns `False` when unconfigured (safe default).

### Phase 4: API Layer (files 10–11)

| Step | File | What |
|------|------|------|
| 4.1 | `api/routers/notebooks.py` | All 15 REST endpoints |
| 4.2 | `api/main.py` | Register `notebooks` router |

**Gate:** `GET /api/notebooks` returns `{"notebooks": []}` — empty list, no crash.

### Phase 5: Frontend (files 12–13)

| Step | File | What |
|------|------|------|
| 5.1 | `web/notebooks.js` | Notebook CRUD, source upload, query UI, snapshot display |
| 5.2 | `web/index.html` | Add sidebar section, detail view panel, chat integration |

**Gate:** Manual test: create notebook → upload source → query → snapshot → delete.

### Phase 6: Research Integration (modify existing files)

| Step | File | What |
|------|------|------|
| 6.1 | `toll/application/research_service.py` | Add notebook source provider loop (Section 10.3) |
| 6.2 | `toll/application/research_service.py` | Add MemoryGraph indexing from notebook notes |

**Gate:** Research task in a workspace with notebooks returns notebook-sourced results.

### Phase 7: Audio Overview (gated)

| Step | File | What |
|------|------|------|
| 7.1 | `toll/adapters/notebooks/notebooklm.py` | Add `generate_audio_overview(notebook_id) → str` method to `NotebookLMProvider` |
| 7.2 | `toll/application/notebook_service.py` | Add `generate_audio_overview(notebook_id) → str` that checks flag, returns audio URL or error |
| 7.3 | `api/routers/notebooks.py` | Add `POST /api/notebooks/{id}/audio-overview` |
| 7.4 | `web/notebooks.js` | Add "Generate Audio Overview" button (visible only when flag enabled) |

**Gate:** Audio overview endpoint returns `{"error": "not implemented"}` when provider strategy is TBD.

### Implementation Order Summary

```
Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5 ──► Phase 6 ──► Phase 7
  4 files      3 files     2 files     2 files     2 files     2 files     4 files
```

Total: **20 files** (12 new, 4 modified, 4 in existing package)

---

## 13. Migration Plan

### 13.1 Migration 0006: New Tables

```sql
-- 0006_notebooks.sql

-- 1. Notebooks
CREATE TABLE IF NOT EXISTS notebooks (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    provider TEXT NOT NULL DEFAULT 'notebooklm',
    provider_notebook_id TEXT,
    provider_meta TEXT DEFAULT '{}',
    sources_count INTEGER DEFAULT 0,
    notes_count INTEGER DEFAULT 0,
    last_synced_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (workspace_id) REFERENCES workspace_state(workspace_id)
);

-- 2. Notebook Sources
CREATE TABLE IF NOT EXISTS notebook_sources (
    id TEXT PRIMARY KEY,
    notebook_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    title TEXT,
    source_uri TEXT NOT NULL,
    content_hash TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    provider_source_id TEXT,
    error_message TEXT,
    file_size INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
);

-- 3. Notebook Notes (with FTS)
CREATE TABLE IF NOT EXISTS notebook_notes (
    id TEXT PRIMARY KEY,
    notebook_id TEXT NOT NULL,
    query_text TEXT NOT NULL,
    response_text TEXT NOT NULL,
    source_ids TEXT DEFAULT '[]',
    provider TEXT NOT NULL DEFAULT 'notebooklm',
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
);

CREATE VIRTUAL TABLE IF NOT EXISTS notebook_notes_fts USING fts5(
    query_text, response_text,
    content='notebook_notes',
    content_rowid='rowid'
);

-- 4. Notebook Snapshots
CREATE TABLE IF NOT EXISTS notebook_snapshots (
    id TEXT PRIMARY KEY,
    notebook_id TEXT NOT NULL,
    label TEXT,
    reason TEXT DEFAULT 'manual',
    source_count INTEGER DEFAULT 0,
    note_count INTEGER DEFAULT 0,
    total_size_bytes INTEGER DEFAULT 0,
    snapshot_data TEXT NOT NULL,
    artifact_id TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_notebooks_workspace ON notebooks(workspace_id);
CREATE INDEX IF NOT EXISTS idx_notebook_sources_notebook ON notebook_sources(notebook_id);
CREATE INDEX IF NOT EXISTS idx_notebook_notes_notebook ON notebook_notes(notebook_id);
CREATE INDEX IF NOT EXISTS idx_notebook_snapshots_notebook ON notebook_snapshots(notebook_id);
```

### 13.2 No Data Migration

All tables are new (no existing data to transform). The migration is pure DDL.

### 13.3 Rollback

```sql
-- 0006_rollback.sql
DROP TABLE IF EXISTS notebook_snapshots;
DROP TABLE IF EXISTS notebook_notes_fts;
DROP TABLE IF EXISTS notebook_notes;
DROP TABLE IF EXISTS notebook_sources;
DROP TABLE IF EXISTS notebooks;
```

### 13.4 Upgrade Path

| From | To | Action |
|------|----|--------|
| `v0.5.5` (current HEAD) | `v0.6.0` | Apply 0006 (no-op for existing data) |
| Future | `v0.6.x` | 0006 is already applied; new migrations append after it |

### 13.5 Edge Cases

| Case | Handling |
|------|----------|
| Migration re-run | All `CREATE TABLE IF NOT EXISTS` — idempotent |
| FTS table rebuild | `DELETE FROM notebook_notes_fts` then `INSERT INTO notebook_notes_fts SELECT rowid, query_text, response_text FROM notebook_notes` — triggered by sync |
| Workspace deleted | `ON DELETE CASCADE` on all foreign keys cleans up notebooks/sources/notes/snapshots |
| Disk full during migration | Migration runs inside a transaction; rollback restores prior state |

---

## 14. Test Plan

### 14.1 Unit Tests

| Test | File | What |
|------|------|------|
| `test_notebook_port_contract` | `tests/core/test_notebook_service.py` | `NotebookPort` method signatures match `NotebookService` expectations |
| `test_create_notebook` | `tests/core/test_notebook_service.py` | CRUD: create, get, update, delete |
| `test_upload_source` | `tests/core/test_notebook_service.py` | Upload saves file, inserts source row, calls port |
| `test_query_notebook` | `tests/core/test_notebook_service.py` | Query returns response, stores note, indexes memory |
| `test_query_cache_hit` | `tests/core/test_notebook_service.py` | Identical query within TTL returns cached note (no port call) |
| `test_sync_sources` | `tests/core/test_notebook_service.py` | Pending sources get uploaded, status → synced |
| `test_sync_pull_notes` | `tests/core/test_notebook_service.py` | New remote notes get stored locally |
| `test_create_snapshot` | `tests/core/test_notebook_service.py` | Snapshot captures all sources + notes, creates artifact |
| `test_auto_snapshot_before_delete` | `tests/core/test_notebook_service.py` | Delete triggers snapshot when flag enabled |
| `test_auto_snapshot_before_sync` | `tests/core/test_notebook_service.py` | Sync triggers snapshot when flag enabled |
| `test_list_snapshots` | `tests/core/test_notebook_service.py` | List returns snapshots ordered by created_at DESC |
| `test_notebook_lifecycle_with_workspace` | `tests/core/test_notebook_service.py` | Full lifecycle: create → upload → query → snapshot → delete |
| `test_feature_flag_gating` | `tests/core/test_feature_flags.py` | `is_enabled("notebooklm_enabled")` returns expected defaults |
| `test_notebook_flag_defaults` | `tests/core/test_feature_flags.py` | All 7 `notebooklm_*` flags resolve correctly |
| `test_provider_selector_notebook` | `tests/core/test_provider_selector.py` | `select_notebook()` returns providers with "notebook" capability |
| `test_audio_overview_gated` | `tests/core/test_notebook_service.py` | `generate_audio_overview` returns error when flag disabled |
| `test_notebook_delete_cascade` | `tests/core/test_notebook_service.py` | Deleting notebook cascades to sources, notes, snapshots |

### 14.2 Adapter Tests

| Test | File | What |
|------|------|------|
| `test_notebooklm_health_unconfigured` | `tests/adapters/test_notebooklm.py` | `health()` returns `False` when no session |
| `test_notebooklm_upload_returns_meta` | `tests/adapters/test_notebooklm.py` | `upload_source()` returns dict with expected keys |
| `test_notebooklm_query_returns_response` | `tests/adapters/test_notebooklm.py` | `query()` returns `NotebookResponse` |
| `test_notebooklm_research_adapter_search` | `tests/adapters/test_notebooklm.py` | `NotebookLMResearchAdapter.search()` returns `ResearchSource` list |

### 14.3 API Integration Tests

| Test | File | What |
|------|------|------|
| `test_list_notebooks_empty` | `tests/api/test_notebooks_api.py` | `GET /api/notebooks` returns `{"notebooks": []}` |
| `test_create_and_get_notebook` | `tests/api/test_notebooks_api.py` | Create → GET returns matching notebook |
| `test_upload_source_multipart` | `tests/api/test_notebooks_api.py` | Upload PDF/text file, verify response |
| `test_query_notebook_endpoint` | `tests/api/test_notebooks_api.py` | POST query returns response shape |
| `test_create_snapshot_api` | `tests/api/test_notebooks_api.py` | POST snapshot returns snapshot + artifact_id |
| `test_delete_notebook_cascade_api` | `tests/api/test_notebooks_api.py` | DELETE cascades, subsequent GET returns 404 |
| `test_notebook_flagged_endpoints_disabled` | `tests/api/test_notebooks_api.py` | All endpoints return 503 when `notebooklm_enabled=False` |
| `test_chat_with_notebook_context` | `tests/test_api.py` | `POST /api/chat` with `notebook_id` returns extended response |

### 14.4 Frontend Smoke Tests

| Test | What |
|------|------|
| Sidebar renders Notebooks section | `notebooklm_enabled` must be `true` for section to appear |
| Create notebook form submits correctly | POST body matches API contract |
| File upload shows progress | Progress bar updates during upload |
| Source list refreshes after upload | New source appears without page reload |
| Query button sends message to notebook | Chat response includes notebook badge |
| Snapshot button creates checkpoint | Snapshot appears in list, artifact link works |
| Audio Overview button hidden by default | Only visible when `notebooklm_audio_overview=true` |
| Delete confirmation appears | Delete requires confirmation (approval-level UX) |

### 14.5 Edge Cases

| Case | Expected Behavior |
|------|-------------------|
| Upload 0-byte file | Rejected; 400 with descriptive error |
| Upload unsupported type | Rejected; 400 with allowed types list |
| Query empty notebook | Graceful: returns "no sources to query" message |
| Create notebook with no workspace_id | 422 validation error |
| Snapshot with 0 sources/notes | Creates snapshot with empty arrays; artifact still created |
| Workspace deletion with notebooks | CASCADE deletes all nested data |
| `strict_local` mode + no cached note | Returns error: "not available offline" |
| Concurrent snapshot + upload | Lock prevents data race; upload after snapshot |
| Migration from pre-0006 | Fresh DDL; no data migration needed |

### 14.6 Test Fixtures

```python
# tests/conftest.py additions

@pytest.fixture
def notebook_service(cm):
    from toll.application.notebook_service import NotebookService
    from toll.application.artifact_service import ArtifactService
    from toll.core.provider_selector import ProviderSelector
    from toll.core.registry import ProviderRegistry
    from toll.core.settings import Settings
    from toll.core.feature_flags import FeatureFlags
    settings = Settings(cm=cm)
    registry = ProviderRegistry(settings)
    flags = FeatureFlags(cm=cm)
    selector = ProviderSelector(registry, settings, flags)
    artifact_svc = ArtifactService(cm)
    return NotebookService(artifact_svc, selector, cm, flags)


@pytest.fixture
def sample_pdf(tmp_path):
    p = tmp_path / "test.pdf"
    p.write_text("%PDF-1.4 mock content")
    return p
```

### 14.7 Test Count Target

| Category | Tests |
|----------|-------|
| Unit (service) | 17 |
| Adapter | 4 |
| API integration | 8 |
| Frontend smoke | 8 |
| **Total** | **37** |

---

## Summary of New Files

| File | Purpose |
|------|---------|
| `toll/ports/notebook.py` | `NotebookPort` + `NotebookResponse` + API models |
| `toll/application/notebook_service.py` | `NotebookService` — orchestration + snapshot + audio |
| `toll/adapters/notebooks/__init__.py` | Package init |
| `toll/adapters/notebooks/notebooklm.py` | `NotebookLMProvider` + `NotebookLMResearchAdapter` |
| `toll/model/migrations/0006_notebooks.sql` | 4 tables (notebooks, sources, notes, snapshots) + FTS + indexes |
| `api/routers/notebooks.py` | Notebook REST endpoints (15 routes) |
| `api/main.py` | Register notebooks router |
| `web/notebooks.js` | Frontend notebook JS module |
| `tests/adapters/test_notebooklm.py` | Adapter unit tests |
| `tests/core/test_notebook_service.py` | Service unit tests (17+) |
| `tests/api/test_notebooks_api.py` | API integration tests (8+) |

## Deferred to Future Sprint

- Notebook export (PDF/Markdown)
- Collaborative notebooks (multi-user)
- Source auto-classification / tagging
- Scheduled sync (cron-based)
- Alternative notebook providers (Obsidian, Notion AI, custom RAG)
