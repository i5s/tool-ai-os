# Sprint 4 Design Review — Application Services & Artifact System

**Goal**: Design the architecture for AI-powered content generation, artifact storage, multi-engine rendering, and provider-aware execution.

**Status**: Design review — no implementation.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Request Lifecycle: Discuss → Plan → Approve → Execute → Artifact](#2-request-lifecycle)
3. [Component 1: Artifact System](#3-component-1-artifact-system)
4. [Component 2: Carousel Engine](#4-component-2-carousel-engine)
5. [Component 3: Report Engine](#5-component-3-report-engine)
6. [Component 4: Presentation Engine](#6-component-4-presentation-engine)
7. [Component 5: OpenDesign Integration](#7-component-5-opendesign-integration)
8. [Component 6: Artifact Storage Strategy](#8-component-6-artifact-storage-strategy)
9. [Component 7: Output Folder Structure](#9-component-7-output-folder-structure)
10. [Component 8: Artifact Retention Policy](#10-component-8-artifact-retention-policy)
11. [Component 9: Provider Selection Strategy](#11-component-9-provider-selection-strategy)
12. [Component 10: ResearchProvider Abstraction (Placeholder)](#12-component-10-researchprovider-abstraction-placeholder)
13. [Component 11: Future Replicate Integration](#13-component-11-future-replicate-integration)
14. [Impact Analysis](#14-impact-analysis)

---

## 1. Architecture Overview

### New Files to Create

```
toll/
  application/
    __init__.py
    artifact_service.py       # Artifact creation + lifecycle
    carousel_service.py       # Carousel generation orchestrator
    report_service.py         # Report generation orchestrator
    presentation_service.py   # Presentation generation orchestrator
    opendesign_service.py     # OpenDesign push + preview
    handler_registry.py       # Registers application handlers with WorkflowEngine
  model/
    artifact.py               # Artifact dataclass + ArtifactType enum + ArtifactStatus enum
  engine/
    renderers/                # NEW: dedicated renderers
      __init__.py
      base.py                 # BaseRenderer ABC
      carousel_renderer.py    # Carousel → HTML
      report_renderer.py      # Report → HTML
      presentation_renderer.py# Presentation → HTML
      code_renderer.py        # Code → syntax-highlighted HTML
      preview_renderer.py     # preview.html + preview.json for all types
    content_machine.py        # REMOVED (split into carousel_service + carousel_renderer)
    reports.py                # REMOVED (split into report_service + report_renderer)
  core/
    provider_selector.py      # NEW: picks which AI provider for a given task type
api/
  routers/
    artifacts.py              # NEW: /api/artifacts CRUD + preview
    engine.py                 # REFACTOR: remove direct ContentMachine/Reports, delegate to application services
```

### Changes to Existing Files

| File | Change |
|------|--------|
| `api/main.py` | Mount `/api/artifacts` router |
| `api/routers/engine.py` | Remove direct `ContentMachine`/`Reports` usage in `/api/chat`; delegate to application service via handler registry |
| `api/routers/planner.py` | After workflow completes, return artifact_id alongside result |
| `api/dependencies.py` | Add `get_artifact_service`, `get_handler_registry` if needed |
| `toll/planner/planner.py` | Add `artifact_export` intent for OpenDesign push |
| `toll/core/feature_flags.py` | Add new feature flags (see §9) |
| `toll/context/engine.py` | Surface recent artifact references in context |
| `toll/workflow/engine.py` | Already has handler registration pattern — used as-is |
| `web/index.html` | Add artifacts list sidebar section |
| `docs/ARCHITECTURE.md` | Move Artifact System from Layer 2 (dormant) to Layer 1 (enabled) |

### File Dependency Graph

```
api/routers/engine.py
  └── toll/application/handler_registry.py
        ├── toll/application/carousel_service.py
        │     ├── toll/engine/renderers/carousel_renderer.py
        │     ├── toll/model/artifact.py
        │     └── toll/core/provider_selector.py
        ├── toll/application/report_service.py
        │     ├── toll/engine/renderers/report_renderer.py
        │     ├── toll/model/artifact.py
        │     └── toll/core/provider_selector.py
        ├── toll/application/presentation_service.py
        │     ├── toll/engine/renderers/presentation_renderer.py
        │     ├── toll/model/artifact.py
        │     └── toll/core/provider_selector.py
        └── toll/application/artifact_service.py
              ├── toll/model/artifact.py
              └── toll/core/connection_manager.py

api/routers/artifacts.py
  └── toll/application/artifact_service.py
        └── toll/model/artifact.py

toll/application/opendesign_service.py
  └── toll/application/artifact_service.py
```

---

## 2. Request Lifecycle

### Discuss → Plan → Approve → Execute → Artifact

```
USER                    API                    PLANNER              WORKFLOW            APPLICATION            ARTIFACT
 │                       │                       │                    │                    │                      │
 │  "إنشاء تقرير عن AI"  │                       │                    │                    │                      │
 │──────────────────────>│                       │                    │                    │                      │
 │                       │  POST /api/chat       │                    │                    │                      │
 │                       │───────────────────────────────────────────>│                    │                      │
 │                       │                       │  plan("إنشاء...")  │                    │                      │
 │                       │                       │<───────────────────│                    │                      │
 │                       │                       │  intent=report     │                    │                      │
 │                       │                       │  level=APPROVAL    │                    │                      │
 │                       │                       │────────────────────>│                    │                      │
 │                       │                       │                    │  create(plan)      │                      │
 │                       │                       │                    │  status=PENDING    │                      │
 │                       │                       │                    │────────────────────│                      │
 │                       │  ⚠️ الموافقة مطلوبة    │                    │                    │                      │
 │                       │<──────────────────────│                    │                    │                      │
 │  approve(workflow_id) │                       │                    │                    │                      │
 │──────────────────────>│  POST /workflows/{id}/approve              │                    │                      │
 │                       │───────────────────────────────────────────>│                    │                      │
 │                       │                       │                    │  status=APPROVED   │                      │
 │                       │                       │                    │────────────────────│                      │
 │                       │                       │                    │  run(id)           │                      │
 │                       │                       │                    │  lookup handler ──>│                      │
 │                       │                       │                    │                    │  report_service      │
 │                       │                       │                    │                    │  .generate(plan)     │
 │                       │                       │                    │                    │  ├─ provider_selector│
 │                       │                       │                    │                    │  ├─ AI.ask(prompt)   │
 │                       │                       │                    │                    │  ├─ render_report()  │
 │                       │                       │                    │                    │  └─ artifact_service │
 │                       │                       │                    │                    │       .create(...)───>│
 │                       │                       │                    │                    │                      │  INSERT artifacts
 │                       │                       │                    │                    │                      │  write HTML to disk
 │                       │                       │                    │                    │<── artifact_id ─────│
 │                       │                       │                    │<── result ─────────│                      │
 │                       │                       │                    │  status=COMPLETED  │                      │
 │                       │  📄 التقرير جاهز       │                    │                    │                      │
 │                       │<──────────────────────│                    │                    │                      │
 │                       │  artifact_id,preview  │                    │                    │                      │
```

### Lifecycle States by Step

| Step | Planner Level | Workflow Status | Action |
|------|--------------|-----------------|--------|
| **Discuss** | — | — | User sends message. Conversation saved. |
| **Plan** | AUTO / PLAN_ONLY / APPROVAL | PENDING | Planner classifies intent. Workflow created. |
| **Approve** | APPROVAL → APPROVED | PENDING → APPROVED | User approves. (SKIP if AUTO) |
| **Execute** | — | APPROVED → RUNNING → COMPLETED/FAILED | Handler registered for intent is invoked. |
| **Artifact** | — | COMPLETED | Result stored as Artifact, rendered to HTML, preview URL returned. |

### Mode Interactions

| Mode | PLAN_ONLY → | APPROVAL → | How artifact created? |
|------|------------|------------|----------------------|
| **Balanced** (default) | PLAN_ONLY workflow, user sees plan, can approve to generate | Must approve → workflow runs → artifact created | After approval |
| **Strict** | Escalated to APPROVAL — plan is hidden behind approval gate | Must approve (same as balanced) | After approval |
| **Fast** | Downgraded to AUTO — plan-only intents skip approval entirely | Still requires approval | Immediately for PLAN_ONLY, after approval for APPROVAL |

### AUTO Intents That Produce Artifacts

Not all AUTO intents produce artifacts (question, summary, translation, brainstorm, explanation, calculation, image_analysis, chat do not). The ones that do:

| Intent | Artifact Type | Provider Selection |
|--------|--------------|-------------------|
| `code_snippet` | `code` | Best LLM |
| `prompt_generation` | `prompt` | Fast LLM |
| `search` | `search_result` | Search adapter |

These are **transient artifacts** — rendered in-chat, optionally saved, low retention priority.

---

## 3. Component 1: Artifact System

### Location: `toll/model/artifact.py`, `toll/application/artifact_service.py`

### Artifact Model

```python
@dataclass
class Artifact:
    id: str
    type: ArtifactType
    status: ArtifactStatus
    title: str
    version: int                       # auto-incrementing per artifact lineage
    parent_artifact_id: str | None     # previous version's ID
    workflow_id: str | None            # Link back to originating workflow
    conversation_id: str | None        # Link back to originating conversation
    content: dict                      # Structured content (varies by type)
    rendered_path: str | None          # Absolute path to rendered output
    preview_url: str | None            # OpenDesign preview URL
    provider: str | None               # Provider used: "opencode", "ollama"
    model: str | None                  # Model used: "qwen2.5", "claude-sonnet-4"
    intent: str | None                 # Planner intent that produced this
    workspace_type: str | None         # "brand", "university", "project", "global"
    workspace_id: str | None           # ID within workspace_type
    tags: list[str]                    # User-supplied or auto-assigned tags
    metadata: dict                     # Tokens, rendering time, flags
    created_at: str
    updated_at: str
    expires_at: str | None             # Retention deadline
```

```python
class ArtifactType(str, Enum):
    CAROUSEL = "carousel"
    REPORT = "report"
    PRESENTATION = "presentation"
    CODE = "code"
    SEARCH_RESULT = "search_result"
    PROMPT = "prompt"
    SOCIAL_POST = "social_post"
    IMAGE = "image"                # Future
    GENERIC = "generic"            # Fallback

class ArtifactStatus(str, Enum):
    DRAFT = "draft"                # Generating / incomplete
    COMPLETED = "completed"        # Ready
    FAILED = "failed"              # Generation error
    ARCHIVED = "archived"          # Past retention, moved to archive
    DELETED = "deleted"            # Soft delete marker
```

### Responsibilities

- CRUD operations on artifacts (SQLite-backed via ConnectionManager)
- Assign artifact IDs (UUID)
- Persist structured content as JSON
- Generate preview files on every render
- Run retention sweeps
- Link artifacts to workflows and conversations
- Return preview URLs

### ArtifactRepository (SQL, in `toll/model/artifact.py` or separate)

```sql
CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    title TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    parent_artifact_id TEXT,
    workflow_id TEXT,
    conversation_id TEXT,
    content TEXT NOT NULL,             -- JSON
    rendered_path TEXT,
    preview_url TEXT,
    provider TEXT,
    model TEXT,
    intent TEXT,
    workspace_type TEXT,
    workspace_id TEXT,
    tags TEXT DEFAULT '[]',            -- JSON array
    metadata TEXT DEFAULT '{}',        -- JSON
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    expires_at TEXT,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id),
    FOREIGN KEY (parent_artifact_id) REFERENCES artifacts(id)
);

CREATE INDEX idx_artifacts_parent ON artifacts(parent_artifact_id);
CREATE INDEX idx_artifacts_workflow ON artifacts(workflow_id);
CREATE INDEX idx_artifacts_expires ON artifacts(expires_at);
```

### Data Flow

```
create_artifact(content, type)
  → INSERT INTO artifacts (status=draft)
  → render(content) → HTML file on disk
  → UPDATE rendered_path, status=completed
  → return Artifact
```

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/artifacts` | List artifacts (filter: type, status, workflow_id) |
| `GET` | `/api/artifacts/{id}` | Get artifact details + content |
| `GET` | `/api/artifacts/{id}/render` | Get rendered HTML content |
| `GET` | `/api/artifacts/{id}/preview` | Get preview URL (redirect or JSON) |
| `DELETE` | `/api/artifacts/{id}` | Delete (soft) artifact |
| `POST` | `/api/artifacts/{id}/archive` | Move to archive |
| `POST` | `/api/artifacts/cleanup` | Trigger retention sweep |

### Feature Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `artifact_system` | `true` **now** | Master switch for the artifact system |

The existing ARCHITECTURE.md marks `artifact_system` as Layer 2 (dormant, default `false`). Sprint 4 promotes it to Layer 1 (always enabled) because the app service layer depends on it.

### Dependencies

- `ConnectionManager` (for SQLite)
- `Settings` (for output paths, retention config)
- No external dependencies

### Future Expansion Path

- Add S3/cloud storage backend (artifact content stored in S3, DB stores path)
- Add artifact versioning (multiple renders of same artifact tracked by version_id)
- Add image artifacts (store image binary in `data/artifacts/{id}/` directory)
- Zip download endpoint

---

## 4. Component 2: Carousel Engine

### Location: `toll/application/carousel_service.py`, `toll/engine/renderers/carousel_renderer.py`

### Responsibilities

- Receive a carousel request (topic, slide count, style, platform)
- Use AI provider to generate slide titles, subtitles, and content
- Return structured content `list[Slide]`
- Hand off to ArtifactService for persistence
- Support future: image generation for slide backgrounds

### Structured Content Shape

```python
@dataclass
class Slide:
    title: str
    subtitle: str
    content: str
    image_prompt: str | None = None   # Future: for Replicate image gen

# Content stored in artifact.content:
# {
#   "slides": [...],
#   "style": "modern" | "minimal" | "bold",
#   "platform": "instagram" | "linkedin" | "twitter",
#   "theme_color": "#38bdf8"
# }
```

### Data Flow

```
CarouselService.generate(topic: str, slides: int = 4, style: str = "modern")
  → AI.ask(prompt=generate_carousel_prompt(topic, slides, style))
  → Parse AI response into list[Slide]
  → ArtifactService.create(type=CAROUSEL, content=slides)
  → CarouselRenderer.render(slides) → HTML
  → ArtifactService.update_rendered_path(artifact_id, path)
  → return Artifact
```

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/carousel/generate` | Generate carousel (creates workflow → artifact) |
| `GET` | `/api/carousel/{id}` | Get carousel content |

These are convenience endpoints. The primary path is through `/api/chat` → Plan → Approve → Execute.

### Feature Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `carousel_engine` | `true` | Enable AI-generated carousels |

### Dependencies

- `ProviderSelector` (for picking LLM)
- `AI.ask()` (via selected provider)
- `ArtifactService`
- `CarouselRenderer`

### Future Expansion Path

- Image generation per slide (Replicate/Fal.ai)
- Interactive carousel (video export via Remotion/Hyperframes)
- Carousel template library

---

## 5. Component 3: Report Engine

### Location: `toll/application/report_service.py`, `toll/engine/renderers/report_renderer.py`

### Responsibilities

- Receive a report request (title, sections, depth, style)
- Use AI provider to generate full report content
- Return structured content `list[Section]`
- Hand off to ArtifactService for persistence

### Structured Content Shape

```python
@dataclass
class Section:
    heading: str
    body: str
    subsections: list[tuple[str, str]] | None = None  # [(subheading, body), ...]

# Content stored in artifact.content:
# {
#   "title": "...",
#   "sections": [...],
#   "style": "academic" | "business" | "technical",
#   "language": "ar" | "en",
#   "metadata": {}
# }
```

### Data Flow

```
ReportService.generate(title: str, style: str = "academic", sections: list[str] | None = None)
  → AI.ask(prompt=generate_report_prompt(title, style, sections))
  → Parse AI response into list[Section]
  → ArtifactService.create(type=REPORT, content=sections)
  → ReportRenderer.render(title, sections) → HTML
  → ArtifactService.update_rendered_path(artifact_id, path)
  → return Artifact
```

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/report/generate` | Generate report (creates workflow → artifact) |
| `GET` | `/api/report/{id}` | Get report content |

Convenience endpoints. Primary path is through `/api/chat`.

### Feature Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `report_engine` | `true` | Enable AI-generated reports |

### Dependencies

- `ProviderSelector`
- `AI.ask()`
- `ArtifactService`
- `ReportRenderer`

### Future Expansion Path

- Multi-language reports (English, French)
- Data-driven reports (chart.js integration in rendered HTML)
- PDF export (via WeasyPrint or puppeteer)

---

## 6. Component 4: Presentation Engine

### Location: `toll/application/presentation_service.py`, `toll/engine/renderers/presentation_renderer.py`

### Responsibilities

- Receive a presentation request (title, slide count, style)
- Use AI provider to generate slide content
- Return structured content `list[PresentationSlide]`
- Hand off to ArtifactService for persistence

### Structured Content Shape

```python
@dataclass
class PresentationSlide:
    title: str
    content: str            # Main slide body
    notes: str | None = None    # Speaker notes (for future export)

# Content stored in artifact.content:
# {
#   "title": "...",
#   "slides": [...],
#   "style": "minimal" | "bold" | "editorial",
#   "language": "ar" | "en",
#   "slide_count": 5
# }
```

### Data Flow

```
PresentationService.generate(title: str, slides: int = 5, style: str = "editorial")
  → AI.ask(prompt=generate_presentation_prompt(title, slides, style))
  → Parse AI response into list[PresentationSlide]
  → ArtifactService.create(type=PRESENTATION, content=slides)
  → PresentationRenderer.render(title, slides) → HTML
  → ArtifactService.update_rendered_path(artifact_id, path)
  → return Artifact
```

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/presentation/generate` | Generate presentation (creates workflow → artifact) |
| `GET` | `/api/presentation/{id}` | Get presentation content |

### Feature Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `presentation_engine` | `true` | Enable AI-generated presentations |

### Dependencies

- `ProviderSelector`
- `AI.ask()`
- `ArtifactService`
- `PresentationRenderer`

### Future Expansion Path

- Speaker notes export
- PPTX export (via python-pptx)
- Slide master / template system
- Presenter mode (teleprompter)

---

## 7. Component 5: OpenDesign Integration

### Location: `toll/application/opendesign_service.py`

### Responsibilities

- Push artifact content to OpenDesign for preview/editing
- Generate OpenDesign preview URLs
- Optionally update artifact when user edits in OpenDesign

### Current State

OpenDesign is listed in ARCHITECTURE.md as a provider (Native mode). The project path is derived from artifact type:

```
{topic}/{artifact_id}/
  index.html    (rendered output)
  content.json  (structured content)
```

### Data Flow (OpenDesign Push)

```
OpenDesignService.push(artifact: Artifact)
  → Create OpenDesign project "{artifact.type}/{artifact.id}"
  → Write rendered HTML as project entry file
  → Write content.json as sidecar
  → Get preview_url from OpenDesign
  → Return preview_url

OpenDesignService.get_preview_url(artifact_id: str) -> str | None
  → Look up stored preview_url
```

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/artifacts/{id}/opendesign-push` | Push artifact to OpenDesign |
| `GET` | `/api/artifacts/{id}/opendesign-preview` | Get OpenDesign preview URL |

### Feature Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `opendesign_integration` | `false` | Master switch for OpenDesign |

Disabled by default — the feature flag is the off-ramp if OpenDesign isn't installed.

### Dependencies

- OpenDesign CLI/API (external)
- `ArtifactService`

### Future Expansion Path

- Bidirectional sync (user edits in OpenDesign → artifact content updated)
- OpenDesign as alternative renderer (render HTML via OpenDesign's skill stack)
- OpenDesign version history

---

## 8. Component 6: Artifact Storage Strategy

### Two Storage Backends

| Backend | What It Stores | Why |
|---------|---------------|-----|
| **SQLite** (via ConnectionManager) | Artifact metadata + structured JSON content | Fast lookups, filtering, linking |
| **File System** | Rendered HTML files | Serveable by FastAPI/static, shareable URLs |

### File System Storage

```
ROOT = toll.core.config.ROOT  # e.g., /Users/S3EED/Claude/Projects/تول

{ROOT}/data/artifacts/
  {artifact_id}/
    index.html         # Rendered output (primary)
    preview.html       # Lightweight preview (visual artifact types)
    preview.json       # Machine-readable preview (all types)
    content.json       # Structured content (redundant copy for portability)
    metadata.json      # Snapshot of artifact DB row
  (no nested type directories — flat by id prevents collisions)
```

### Preview Files

Every artifact generates **both** preview formats at render time:

| Format | Audience | Content |
|--------|----------|---------|
| `preview.html` | User browsing web dashboard | First slide / TOC + first section / code snippet + "View full" link |
| `preview.json` | API consumers, CLI, automation | `{id, type, title, status, created_at, provider, model, tags, summary, full_url, preview_url}` |

The preview is generated by `PreviewRenderer` which dispatches to type-specific preview logic (see §8.5).

The `preview_url` column in the artifact DB row stores `{base_url}/data/artifacts/{id}/preview.html` (or `.json` for non-visual types).

### Why Flat-By-ID?

- Eliminates naming collisions
- Makes archive/delete operations atomic (rm -rf {id})
- No need for path migrations when renaming artifact types
- Easy to rsync to backup/archive locations

### Static File Serving

FastAPI mounts `{ROOT}/data/` as a static directory at a dedicated prefix:

```python
from fastapi.staticfiles import StaticFiles
app.mount("/data", StaticFiles(directory=str(ROOT / "data")), name="data")
```

This makes each artifact accessible at `/data/artifacts/{id}/index.html`.

### Performance Considerations

- SQLite handles all queries — filesystem is write-once, read-rarely
- No file system scanning except during startup validation
- Retention sweep walks DB `expires_at` column, not the filesystem

### PreviewRenderer

```python
# toll/engine/renderers/preview_renderer.py

class PreviewRenderer:
    """Generates preview.html and preview.json for any artifact type."""

    def render_html(self, artifact: Artifact) -> str:
        if artifact.type == ArtifactType.CAROUSEL:
            return self._carousel_preview(artifact)
        if artifact.type == ArtifactType.REPORT:
            return self._report_preview(artifact)
        if artifact.type == ArtifactType.PRESENTATION:
            return self._presentation_preview(artifact)
        if artifact.type == ArtifactType.CODE:
            return self._code_preview(artifact)
        return self._generic_preview(artifact)

    def render_json(self, artifact: Artifact) -> dict:
        return {
            "id": artifact.id,
            "type": artifact.type.value,
            "title": artifact.title,
            "status": artifact.status.value,
            "version": artifact.version,
            "created_at": artifact.created_at,
            "provider": artifact.provider,
            "model": artifact.model,
            "intent": artifact.intent,
            "tags": artifact.tags,
            "summary": self._summarize(artifact),
            "full_url": f"/data/artifacts/{artifact.id}/index.html",
            "preview_url": f"/data/artifacts/{artifact.id}/preview.html",
        }
```

Each type-specific preview HTML includes a minimal, fast-loading page with a link to the full artifact.
Exact templates are defined at implementation time and follow the corresponding `*Renderer`'s visual language.

---

## 9. Component 7: Output Folder Structure

### Complete layout

```
{ROOT}/
├── toll/
├── api/
├── web/
└── data/
    ├── toll.db                      # SQLite database (unchanged)
    └── artifacts/                   # Generated output files
        ├── a1b2c3d4-.../
        │   ├── index.html           # Rendered artifact
        │   ├── content.json         # Structured content
        │   └── metadata.json        # DB row snapshot
        ├── e5f6g7h8-.../
        │   ├── index.html
        │   ├── content.json
        │   └── metadata.json
        └── archive/                 # Past-retention artifacts (compressed)
            ├── a1b2c3d4-....tar.gz
            └── ...
```

### Migration from current output

Current output goes to `~/Claude/Projects/الموقع/`. Sprint 4:

1. New artifacts go to `{ROOT}/data/artifacts/{uuid}/`
2. Old files in `~/الموقع/` are not migrated — they are orphaned and readable but not tracked in the artifact system
3. The `Settings.website_path` config key becomes deprecated; its only remaining use is serving legacy files

### Static Mount Points

| Prefix | Source | Purpose |
|--------|--------|---------|
| `/data` | `{ROOT}/data/` | Artifact rendering + DB |
| `/` (existing) | `{ROOT}/web/` | SPA dashboard |
| `/static/legacy` (optional) | `~/Claude/Projects/الموقع/` | Legacy files |

---

## 10. Component 8: Artifact Retention Policy

### Policy Matrix

| Artifact Status | Default TTL | Configurable? | Archive Action |
|----------------|-------------|---------------|----------------|
| `draft` | 7 days | Yes | Delete files + soft-delete DB row |
| `completed` | 90 days | Yes | Compress → `data/artifacts/archive/`, soft-delete DB row |
| `failed` | 1 day | Yes | Delete all traces |
| `archived` | Never (permanent) | Yes | Keep in archive folder |
| (favorited) | Never | — | Skip retention (marked in metadata) |

### Configuration

```python
# Settings defaults for retention
"artifact_retention_draft_days": "7",
"artifact_retention_completed_days": "90",
"artifact_retention_failed_hours": "24",
"artifact_archive_enabled": "true",
```

### Implementation: `RetentionService`

```python
class RetentionService:
    def __init__(self, cm: ConnectionManager, settings: Settings):
        self.cm = cm
        self.settings = settings

    def sweep(self):
        """Called on startup or by POST /api/artifacts/cleanup."""
        now = datetime.now(timezone.utc).isoformat()
        # Draft: expires_at = created_at + 7d
        # Completed: expires_at = created_at + 90d
        # Failed: expires_at = created_at + 1d
        expired = self.cm.connection.execute(
            "SELECT * FROM artifacts WHERE expires_at < ? AND status != 'archived'",
            (now,),
        ).fetchall()
        for row in expired:
            self._archive_or_delete(row)
```

### Sweep Triggers

- On API server startup (after workflow recovery)
- On demand via `POST /api/artifacts/cleanup`
- Optionally: cron job (macOS `launchd` or systemd timer)

### Archive Format

```bash
# Completed artifact at sweep time:
tar -czf data/artifacts/archive/{id}.tar.gz -C data/artifacts/{id} .
rm -rf data/artifacts/{id}
UPDATE artifacts SET status='archived', rendered_path=NULL WHERE id=?
```

---

## 11. Component 9: Provider Selection Strategy

### Location: `toll/core/provider_selector.py`

### Principle

No hardcoded provider-to-task mappings. Selection is a four-factor resolution at runtime:

```
ProviderSelector.select(task_type) → provider_name
                           ↑
            ┌──────────────┼──────────────┐
            │              │              │
     Task Type      Availability    User Preference
            │              │              │
            └──────────────┼──────────────┘
                           │
                    Feature Flags
```

### The Four Factors

| Factor | Source | Evaluation |
|--------|--------|------------|
| **Task Type** | `ArtifactType` enum passed by caller | Report, carousel, presentation, code, image |
| **Provider Availability** | `ProviderRegistry.available_llm()` | Online + within rate limit |
| **User Preference** | Settings `provider_for_{task_type}` | Explicit user override |
| **Feature Flags** | `FeatureFlags.is_enabled("provider_opencode")` | Adapter-level kill switch |

### Design: `ProviderSelector`

```python
@dataclass
class ProviderCandidate:
    provider_name: str
    quality_score: float         # 0.0–1.0 from most recent usage
    available: bool              # online + under rate limit
    preferred_by_user: bool      # user explicitly set this provider for this task type
    allowed_by_flag: bool        # feature flag permits this provider

class ProviderSelector:
    def __init__(self, registry: ProviderRegistry, settings: Settings, flags: FeatureFlags):
        self.registry = registry
        self.settings = settings
        self.flags = flags

    def select(self, task_type: ArtifactType, prefer: str | None = None) -> str | None:
        available = self.registry.available_llm()  # returns list of provider names
        user_pref = prefer or self.settings.get(f"provider_for_{task_type.value}")

        candidates: list[ProviderCandidate] = []
        for name in available:
            candidates.append(ProviderCandidate(
                provider_name=name,
                quality_score=self._quality_score(name, task_type),
                available=True,  # confirmed by registry
                preferred_by_user=(name == user_pref),
                allowed_by_flag=self.flags.is_enabled(f"provider_{name}", default=True),
            ))

        if not candidates:
            return None

        # Score each candidate (higher is better)
        def score(c: ProviderCandidate) -> float:
            s = 0.0
            if c.allowed_by_flag:
                s += 10.0
            if c.preferred_by_user:
                s += 20.0                     # user override dominates
            s += c.quality_score * 5.0        # quality matters
            return s

        candidates.sort(key=score, reverse=True)
        return candidates[0].provider_name

    def _quality_score(self, provider: str, task_type: ArtifactType) -> float:
        """Learns from past artifact metadata. For Sprint 4 uses static defaults."""
        SCORES: dict[str, float] = {
            "opencode": 0.9,
            "ollama": 0.5,
        }
        return SCORES.get(provider, 0.3)
```

### User Preference Settings

| Setting | Default | Purpose |
|---------|---------|---------|
| `provider_for_report` | `""` (auto) | Pin a specific provider for reports |
| `provider_for_presentation` | `""` (auto) | Pin a specific provider for presentations |
| `provider_for_carousel` | `""` (auto) | Pin a specific provider for carousels |
| `provider_for_code` | `""` (auto) | Pin a specific provider for code |

Empty string means "auto-select from available + quality scores."

### Feature Flag Interaction

| Flag | Effect on Selection |
|------|-------------------|
| `provider_opencode=false` | OpenCode excluded from candidate list |
| `provider_ollama=false` | Ollama excluded from candidate list |
| `provider_replicate=false` | (Future) excluded from candidate list |

A user preference for a disabled provider is noted in `preferred_by_user=true` but `allowed_by_flag=false` — the selector logs a warning and picks the next best candidate.

### Fallback Behavior

1. Build candidate list from available providers that pass feature flags
2. Score + rank candidates
3. Return top candidate
4. If all fail at execution time (rate limit, offline), re-call `select()` to get next candidate
5. If candidate list is empty or all exhausted → mark artifact as FAILED, return error: "No available provider for {task_type}"

### Future scoring improvement

Quality scores can be learned from artifact completion metadata:

```python
# Future: update quality score from outcome
def record_outcome(self, provider: str, task_type: ArtifactType, success: bool, duration_ms: int):
    # Adjust quality_score in persistent store
    ...
```

### AI Prompt Templates

`toll/engine/prompt_gen.py` already has basic templates. These need expanding per service:

```
Carousel prompt:
"Write {slide_count} slides for a carousel about {topic} in {language}.
Style: {style}. Return each slide as: | Title | Subtitle | Content |"

Report prompt:
"Write a {style} report titled '{title}' with sections: {sections}.
Language: {language}. Return each section as: | Heading | Body |"

Presentation prompt:
"Write {slide_count} slides for a presentation titled '{title}'.
Style: {style}. Language: {language}.
Return each slide as: | Title | Content |"
```

---

## 12. Component 10: ResearchProvider Abstraction (Placeholder)

### Location: `toll/ports/research.py` (interface only)

### Motivation

Academic content generation (reports, study plans, research plans) may eventually need access to specialized research tools: citation databases, academic search, NotebookLM-style source synthesis. Sprint 4 defines the contract; Sprint 5+ implements adapters.

### Port Interface

```python
# toll/ports/research.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ResearchSource:
    title: str
    url: str | None
    authors: list[str]
    year: int | None
    citation: str          # Formatted citation string (MLA, APA, etc.)
    relevance_score: float  # 0.0–1.0

@dataclass
class ResearchQuery:
    query: str
    max_sources: int = 10
    style: str = "apa"           # Citation style
    include_full_text: bool = False

@dataclass
class ResearchResult:
    sources: list[ResearchSource]
    summary: str | None           # AI-generated synthesis of sources
    error: str | None

class ResearchProvider(ABC):
    @abstractmethod
    def search(self, query: ResearchQuery) -> ResearchResult:
        ...

    @abstractmethod
    def cite(self, source: ResearchSource, style: str = "apa") -> str:
        """Generate a formatted citation string."""
        ...

    @abstractmethod
    def synthesize(self, sources: list[ResearchSource], topic: str) -> str:
        """Generate a synthesized summary from multiple sources."""
        ...
```

### Integration Points

The ResearchProvider plugs into the application service layer when generating academic content:

```
ReportService.generate(title, style="academic")
  → if style == "academic" and research_provider available:
      → research_provider.search(query)
      → enrich section content with citations
      → include bibliography in rendered output
```

### Future Adapters (Not Implemented in Sprint 4)

| Adapter | Purpose | Provider |
|---------|---------|----------|
| `NotebookLM` | Source synthesis, audio overviews | Google NotebookLM |
| `Google Scholar` | Academic paper search | Scholar API / scraping |
| `Semantic Scholar` | AI-powered academic search | Semantic Scholar API |
| `Zotero` | Citation management | Zotero API |
| `Crossref` | DOI resolution, citation lookup | Crossref REST API |
| `ArXiv` | Pre-print search | ArXiv API |

### Feature Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `research_provider` | `false` | Master switch for research tools |

### What Sprint 4 Does vs Doesn't Do

| Action | Sprint 4 Scope |
|--------|---------------|
| Define `ResearchPort` ABC | ✅ Yes (interface only) |
| Add `research_provider` flag | ✅ Yes (disabled) |
| Implement any research adapter | ❌ No (future sprint) |
| Wire into report service | ❌ No (future sprint when adapter exists) |

---

## 13. Component 11: Future Replicate Integration

### Vision

Enable image generation for artifact types that need visuals — carousel slide backgrounds, report cover images, presentation illustrations.

### Integration Point

Replicate plugs into the **rendering pipeline**, not the application service layer:

```
Application Service (produces content)
  → Renderer (produces HTML)
      ├── If image needed → call ReplicateImageProvider
      └── Embed returned image URL in HTML
```

### Provider Abstraction (Future)

```python
# toll/ports/image.py
class ImageProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, style: str = "") -> str:
        """Generate image, return URL or path."""
        ...

# toll/adapters/image/replicate.py (future)
class ReplicateImageProvider(ImageProvider):
    def generate(self, prompt: str, style: str = "") -> str:
        # POST to Replicate API
        # Return image URL
        ...
```

For Sprint 4, the `ImagePort` is defined but not implemented. The renderers check a feature flag:

```python
if feature_flags.is_enabled("image_generation"):
    image_url = image_provider.generate(slide.image_prompt)
else:
    image_url = ""  # Use CSS gradient placeholder
```

### Replicate-Specific Shape

```python
REPLICATE_MODELS = {
    "flux": "black-forest-labs/flux-schnell",      # Fast, good for carousels
    "sdxl": "stability-ai/sdxl",                    # Versatile, good for reports
    "playground": "playground-v2.5",               # Clean, good for presentations
}
```

### Feature Flags (Future)

| Flag | Default | Purpose |
|------|---------|---------|
| `image_generation` | `false` | Master switch for AI images in artifacts |
| `provider_replicate` | `false` | Enable Replicate adapter |

### What Sprint 4 Does vs Doesn't Do for Replicate

| Action | Sprint 4 Scope |
|--------|---------------|
| Define `ImagePort` ABC | ✅ Yes (interface only) |
| Add `image_replicate` flag | ✅ Yes (disabled) |
| Implement Replicate adapter | ❌ No (future sprint) |
| Embed image placeholders in renderers | ✅ Yes (CSS gradients, SVG placeholders) |

---

## 14. Impact Analysis

### Files Created (new)

| File | Lines (est.) | Complexity |
|------|-------------|------------|
| `toll/model/artifact.py` | 60 | Low — dataclasses + enums |
| `toll/application/artifact_service.py` | 120 | Medium — CRUD + business logic |
| `toll/application/carousel_service.py` | 80 | Medium — AI + parsing |
| `toll/application/report_service.py` | 80 | Medium — AI + parsing |
| `toll/application/presentation_service.py` | 80 | Medium — AI + parsing |
| `toll/application/opendesign_service.py` | 50 | Low — API wrapper |
| `toll/application/handler_registry.py` | 40 | Low — wiring |
| `toll/engine/renderers/__init__.py` | 2 | Trivial |
| `toll/engine/renderers/base.py` | 15 | Low — ABC |
| `toll/engine/renderers/carousel_renderer.py` | 90 | Medium — HTML template |
| `toll/engine/renderers/report_renderer.py` | 90 | Medium — HTML template |
| `toll/engine/renderers/presentation_renderer.py` | 90 | Medium — HTML template |
| `toll/engine/renderers/code_renderer.py` | 40 | Low — syntax highlighting |
| `toll/core/provider_selector.py` | 70 | Low — config + heuristics |
| `api/routers/artifacts.py` | 80 | Low — CRUD endpoints |
| Migration: `0004_artifacts.sql` | 20 | Trivial |
| **Total new files** | **~1007** | |

### Files Modified

| File | Change Magnitude |
|------|-----------------|
| `api/main.py` | +2 lines (mount artifacts router) |
| `api/routers/engine.py` | Medium — remove ContentMachine/Reports references, use service calls |
| `api/dependencies.py` | +3 lines (get_artifact_service) |
| `toll/core/feature_flags.py` | +8 lines (new flags) |
| `toll/core/config.py` | +6 lines (ARTIFACTS_PATH, ARCHIVE_PATH) |
| `web/index.html` | Medium — add artifacts list sidebar section |
| `docs/ARCHITECTURE.md` | Move artifact_system to Layer 1 |

### Files Removed

| File | Replacement |
|------|------------|
| `toll/engine/content_machine.py` | `carousel_service.py` + `carousel_renderer.py` |
| `toll/engine/reports.py` | `report_service.py` + `presentation_service.py` + their renderers |

### Files That Stay but Change Internally

| File | What Changes |
|------|-------------|
| `toll/engine/prompt_gen.py` | Updated templates with structured output format |

### Migration Path

1. Add migration `0004_artifacts.sql` (CREATE TABLE artifacts)
2. Deploy new files
3. Enable `artifact_system` flag (change default from `false` to `true`)
4. Old files in `~/الموقع/` become read-only legacy — no migration needed
5. Run `retention_service.sweep()` on first startup to clean any incomplete drafts

### Testing Impact

| Test File | Action | Tests |
|-----------|--------|-------|
| `tests/core/test_artifact_service.py` | **NEW** | 8 tests: CRUD, render, sweep |
| `tests/core/test_artifact_model.py` | **NEW** | 3 tests: enums, serialization |
| `tests/core/test_provider_selector.py` | **NEW** | 5 tests: selection, override, fallback |
| `tests/application/test_carousel_service.py` | **NEW** | 4 tests: generate, parse, render |
| `tests/application/test_report_service.py` | **NEW** | 4 tests: generate, parse, render |
| `tests/application/test_presentation_service.py` | **NEW** | 4 tests: generate, parse, render |
| `tests/application/test_opendesign_service.py` | **NEW** | 2 tests: push, preview |
| `tests/application/test_handler_registry.py` | **NEW** | 2 tests: registration, dispatch |
| `tests/engine/test_renderers.py` | **NEW** | 6 tests: each renderer |
| `tests/test_api.py` | **MODIFY** | +4 tests: artifact endpoints |
| `tests/core/test_conftest.py` (fixtures) | **MODIFY** | +1 fixture: sample artifact |
| `tests/core/test_planner.py` | **MODIFY** | +2 tests: artifact_export intent |

### Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| AI-generated content is low-quality | Medium | Provider selector prefers better LLM for reports/presentations |
| Structured content parsing from AI fails | Low-Medium | Parse with regex fallback; store raw text as backup |
| Carousel HTML loses visual quality | Low | CarouselRenderer uses existing proven template |
| OpenDesign not installed | Low | Feature-gated; graceful fallback |
| DB migration conflicts with existing data | Low | New table, no schema changes to existing tables |
| Performance: many small artifact files | Low | Flat-by-ID directory; no filesystem scanning |
| Retention sweep deletes user content prematurely | Low | Favorited artifacts skipped; archive before delete; configurable TTLs |

---

## Summary: What Sprint 4 Delivers

| Capability | Current (Sprint 3.5) | Sprint 4 |
|-----------|---------------------|----------|
| Content generation | Static HTML templates | AI-powered via dynamic provider selector |
| Output storage | Dumped to `~/الموقع/` | Structured `data/artifacts/{uuid}/` |
| Artifact tracking | History table only | `artifacts` table with full CRUD |
| Artifact versioning | None | `version` + `parent_artifact_id` lineage |
| Artifact metadata | None | provider, model, workspace, intent, tags |
| Workflow → artifact link | None | `workflow_id` foreign key |
| Provider selection | Single AI.ask() | Task type + availability + user pref + flags |
| OpenDesign preview | File paths only | Feature-flagged push + preview URL |
| Rendering | Inline in service classes | Dedicated renderer classes + PreviewRenderer |
| Image generation | None | Port defined, placeholder path, flagged |
| Research tools | None | ResearchProvider ABC defined (future adapters) |
| Retention | None | Configurable TTL + archive + sweep |
| Static serving | None | `/data/artifacts/{id}/index.html` |

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Artifact IDs are UUIDs | No collisions, no sequential guessing, no path conflicts |
| Content stored as JSON in SQLite | Queryable, filterable, no filesystem scan needed |
| Rendered HTML on filesystem | Efficient static serving, shareable URLs |
| Flat-by-id artifact storage | No migration on type rename, atomic archive |
| Renderers are separate classes | Each type has distinct HTML structure; single-file renderers stay under 100 lines |
| Provider selection is config per task type | User may want cheap carousels but high-quality reports |
| OpenDesign integration is feature-flagged | Not all environments have OpenDesign installed |
| Retention defaults favor safety | 90d for completed, archive before delete, favorites skip sweep |
| `prompt_gen.py` stays but gets updated templates | It serves a different use case (generating prompts FOR the AI, not generating content) |
| ContentMachine/Reports removed, not refactored | Their current code is placeholder templates; replacing with AI-powered services makes more sense than inheriting static HTML |
