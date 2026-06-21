# Sprint 4 Report — Application Services & Artifact System

**Date:** 2026-06-21  
**Status:** Complete  
**Tests:** 127 passed, 2 skipped (+35 new tests)

---

## Summary

Sprint 4 implemented a full application services layer with an artifact system supporting AI-powered content generation, versioning, preview, and provider-aware execution. The old monolithic ContentMachine/Reports are now wrapped by domain services accessed through a HandlerRegistry.

---

## What Was Built

### 1. Artifact Model & Persistence

| Component | File | Description |
|---|---|---|
| Artifact dataclass | `toll/model/artifact.py` | Type, status, version, metadata, tags, provider, model, intent, workspace, preview_url, parent_artifact_id |
| ArtifactRepository | `toll/model/artifact.py` | CRUD, versioning, soft-delete, type/status/workflow filtering |
| Migration 0004 | `toll/model/migrations/0004_artifacts.sql` | `artifacts` table with indexes on `type`, `status`, `workflow_id`, `parent_artifact_id` |

### 2. Artifact Service

`toll/application/artifact_service.py` — Orchestrates DB persistence + filesystem writes:

- `create()` / `update()` — persists artifact + writes `index.html`, `content.json`, `metadata.json`
- `write_preview()` — writes `preview.html` + `preview.json`
- `archive()` — tars artifact directory, marks status `ARCHIVED`
- `get_rendered_path()` / `get_preview_html()` / `get_preview_json()` — retrieval methods

### 3. Domain Services (AI + Render + Preview)

| Service | File | Feature Flag |
|---|---|---|
| CarouselService | `toll/application/carousel_service.py` | `carousel_engine` |
| ReportService | `toll/application/report_service.py` | `report_engine` |
| PresentationService | `toll/application/presentation_service.py` | `presentation_engine` |
| OpenDesignService | `toll/application/opendesign_service.py` | `opendesign` (disabled) |

Each service calls AI provider → render HTML → write artifact + preview in one operation.

### 4. Renderers

| Renderer | File | Output |
|---|---|---|
| BaseRenderer (ABC) | `toll/engine/renderers/base.py` | Abstract `render()` method |
| CarouselRenderer | `toll/engine/renderers/carousel_renderer.py` | RTL carousel with dot navigation |
| ReportRenderer | `toll/engine/renderers/report_renderer.py` | RTL academic report with sections |
| PresentationRenderer | `toll/engine/renderers/presentation_renderer.py` | RTL slide deck with numbered navigation |
| CodeRenderer | `toll/engine/renderers/code_renderer.py` | Syntax-highlighted code block |
| PreviewRenderer | `toll/engine/renderers/preview_renderer.py` | Type-specific preview HTML + JSON summary |

### 5. ProviderSelector

`toll/core/provider_selector.py` — Dynamic four-factor provider selection:

1. **Task Type** — carousel/report/presentation have compatible providers
2. **Provider Availability** — only `available` or `degraded` providers
3. **User Preference** — `+20` score for user-preferred provider
4. **Feature Flags** — provider must be enabled

Scoring: quality × 50 + (user_pref ? 20 : 0). No hardcoded mappings.

### 6. ResearchProvider Placeholder

`toll/ports/research.py` — ABC with `ResearchQuery`, `ResearchSource`, `ResearchResult`. Feature-flagged off, not implemented.

### 7. HandlerRegistry

`toll/application/handler_registry.py` — Wires application services into WorkflowEngine:

- `register_handlers(wf, cm)` — registers `carousel`, `report`, `presentation` handlers
- Each handler is gated by its feature flag

### 8. API Endpoints

| Endpoint | Router | Description |
|---|---|---|
| `GET /api/artifacts` | `api/routers/artifacts.py` | List artifacts (filterable) |
| `GET /api/artifacts/{id}` | `api/routers/artifacts.py` | Get artifact details |
| `GET /api/artifacts/{id}/content` | `api/routers/artifacts.py` | Get artifact content |
| `GET /api/artifacts/{id}/render` | `api/routers/artifacts.py` | Get rendered HTML |
| `GET /api/artifacts/{id}/preview` | `api/routers/artifacts.py` | Get preview HTML |
| `DELETE /api/artifacts/{id}` | `api/routers/artifacts.py` | Soft-delete artifact |

### 9. Legacy Code

The old `toll/engine/content_machine.py` and `toll/engine/reports.py` still exist and are imported by:
- `bot/telegram.py` — direct instantiation
- `cli/main.py` — direct instantiation
- `api/routers/engine.py` — used for non-carousel/report/presentation endpoints

**These files should remain** until the CLI and Telegram bot are migrated to use application services.

---

## Feature Flags Added

| Flag | Default | Description |
|---|---|---|
| `artifact_system` | enabled | Enables artifact CRUD API |
| `carousel_engine` | enabled | Enables AI carousel generation |
| `report_engine` | enabled | Enables AI report generation |
| `presentation_engine` | enabled | Enables AI presentation generation |
| `opendesign` | disabled | OpenDesign CLI integration |
| `research_provider` | disabled | ResearchProvider placeholder |
| `image_provider` | disabled | AI image generation |
| `replicate_provider` | disabled | Replicate API integration |

---

## Architecture

```
                     ┌──────────────┐
                     │  Workflow    │
                     │   Engine     │
                     └──────┬───────┘
                            │
                     ┌──────┴───────┐
                     │ HandlerReg.  │
                     └──────┬───────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                  │
   ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐
   │ Carousel    │  │ Report      │  │ Present     │
   │ Service     │  │ Service     │  │ Service     │
   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
          │                 │                  │
          └─────────────────┼─────────────────┘
                            │
                     ┌──────┴──────┐
                     │ Artifact    │
                     │ Service     │
                     └──────┬──────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
        ┌─────┴────┐  ┌────┴────┐  ┌────┴────┐
        │SQLite    │  │Filesys  │  │Preview  │
        │(repo)    │  │(HTML/   │  │Renderer │
        │          │  │ JSON)   │  │         │
        └──────────┘  └─────────┘  └─────────┘
```

---

## Test Coverage

| Area | Tests |
|---|---|
| Artifact model (dataclass + repository) | 10 |
| ArtifactService | 6 |
| Base renderer | 2 |
| Renderers (carousel, report, presentation, code, preview) | 7 |
| HandlerRegistry | 1 |
| ProviderSelector | 2 |
| Artifacts API | 5 |
| **Total new tests** | **35** |
| **Total existing** | **92** |
| **Grand total** | **127** |
