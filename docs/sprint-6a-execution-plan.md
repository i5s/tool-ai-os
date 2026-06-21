# Sprint 6A — Execution Plan

**Status:** Approved — Awaiting Implementation  
**Supersedes:** `docs/sprint-6-media-layer-design.md`, `docs/sprint-6a-model-registry-benchmark-design.md`  
**Target:** v0.7.0-zuno  

---

## 1. Sprint Goal

Deliver the **Media Layer Foundation** as a first-class platform capability, paired with a **Model Registry** for dynamic model discovery and a **Benchmark Lab** for data-driven model comparison.

The existing flat chat UI is restructured into a navigable sidebar (Chat, Research, Projects, Models, Lab, Settings) — codenamed **ZUNO**.

---

## 2. Scope

### In Scope (Implement)

| Area | Deliverables |
|------|-------------|
| **Navigation** | Sidebar restructure: Chat / Research / Projects / Models / Lab / Settings |
| **Media Storage** | Filesystem storage layer (`data/media/`), `FsMediaStorage` adapter |
| **Media Artifacts** | `IMAGE_GEN`, `VIDEO` types in `ArtifactType` enum; migration 0010 |
| **ImageProvider port** | `MediaPort` abstract with `generate()`, `MediaRequest`/`MediaResult` dataclasses |
| **VideoProvider port** | Same `MediaPort` extended for video (duration, fps, style) |
| **MediaService** | Generate image/video → store → create artifact → return result |
| **Model Registry** | SQLite-backed model catalog; dynamic registration; seed data; API |
| **Benchmark Lab** | Suite CRUD, single-run, comparison, leaderboard; AI quality scoring (opt-in) |
| **ProviderSelector** | Refactored to support benchmark-backed scoring (data-driven) |
| **Replicate adapter** | First media provider adapter (image: Flux Schnell, Flux Pro, SDXL) |
| **Tests** | ~40 tests across all subsystems |

### Out of Scope (Do NOT Implement)

| Area | Reason |
|------|--------|
| Veo integration | Provider not available; stub only if needed |
| Runway integration | Provider not available; stub only if needed |
| Audio generation | Standalone feature; deferred to post-6A |
| Character consistency | Advanced workflow; deferred |
| Advanced workflows | Composition pipelines, multi-step; deferred |
| OpenAI adapter | API key dependency; deferred to post-6A |
| Fal adapter | Provider not yet evaluated; deferred |
| OpenDesign adapter | Different domain; deferred |

---

## 3. ZUNO Navigation

### 3.1 Planned Sidebar Structure

```
┌─────────────────────┐
│  ZUNO      [logo]   │
├─────────────────────┤
│                     │
│  💬 Chat            │  ← conversations, messages
│  🔬 Research        │  ← research artifacts, notebooks
│  📁 Projects        │  ← workspace manager, project files
│  🧠 Models          │  ← model registry, registration
│  ⚗️ Lab             │  ← benchmark suites, comparisons
│  ⚙️ Settings        │  ← app settings, providers
│                     │
├─────────────────────┤
│  Workspace: [sel]   │
│  [New Chat]         │
└─────────────────────┘
```

### 3.2 View Switching

- Each nav item switches the main content area to its dedicated view
- Chat view: existing conversation UI (unchanged)
- Research view: research artifact browser (existing data, new layout)
- Projects view: workspace manager (existing data, new layout)
- Models view: model catalog table + register form (new)
- Lab view: benchmark suites + comparison dashboard (new)
- Settings view: settings modal as full view (moved from modal)

### 3.3 JavaScript State

```javascript
const ZUNO = {
    view: 'chat',  // 'chat' | 'research' | 'projects' | 'models' | 'lab' | 'settings'
    // ...
};

function switchView(view) {
    ZUNO.view = view;
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(`view-${view}`).classList.add('active');
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector(`.nav-item[data-view="${view}"]`).classList.add('active');
}
```

---

## 4. Architecture

### 4.1 Layer Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     ZUNO Web UI (Sidebar Nav)                  │
│  Chat │ Research │ Projects │ Models │ Lab │ Settings          │
├──────────────────────────────────────────────────────────────┤
│                     Application Layer                          │
│  MediaService  │  ModelRegistryService  │  BenchmarkService    │
├──────────────────────────────────────────────────────────────┤
│                     Ports (Abstract)                           │
│  MediaPort (Image / Video)  │  ModelRegistryPort               │
├──────────────────────────────────────────────────────────────┤
│                     Adapter Layer                               │
│  ReplicateMediaAdapter  │  FsMediaStorage                      │
├──────────────────────────────────────────────────────────────┤
│                     Storage Layer                               │
│  SQLite (migrations 0010 + 0011)  │  data/media/  │  data/bench/│
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Model → Provider Resolution Flow

```
User: "generate image with flux-schnell"
  → MediaService._resolve_model("replicate:flux-schnell")
    → ModelRegistryService.get("replicate:flux-schnell")
      → returns Model{provider="replicate", provider_model_id="...", ...}
  → MediaService._get_adapter("replicate")
    → returns ReplicateMediaAdapter
  → adapter.generate(MediaRequest(provider_model_id="black-forest-labs/flux-schnell", ...))
  → MediaResult → artifact → response
```

### 4.3 Benchmark → ProviderSelector Flow (Future)

```
ProviderSelector.select(ArtifactType.IMAGE_GEN)
  → currently: hardcoded _quality_score dict
  → future: BenchmarkService.get_best(media_type="image", prefer_quality=True)
    → queries benchmark_runs aggregate stats
    → returns ranked model list
    → selector picks top available
```

Phase 1: `ProviderSelector` checks registry for available models, keeps hardcoded fallback scores.  
Phase 2 (post-6A): `ProviderSelector` queries benchmark aggregates; hardcoded scores become fallback when no benchmark data exists.

---

## 5. Migration Plan

Two migrations, applied in order:

### Migration 0010 — Media Storage

```sql
CREATE TABLE IF NOT EXISTS media_meta (
    id TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL,
    media_type TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT,
    prompt TEXT NOT NULL,
    negative_prompt TEXT,
    width INTEGER,
    height INTEGER,
    duration_ms INTEGER,
    file_size_bytes INTEGER NOT NULL,
    content_type TEXT NOT NULL,
    seed INTEGER,
    style TEXT,
    error TEXT,
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_media_artifact_id ON media_meta(artifact_id);
CREATE INDEX idx_media_type ON media_meta(media_type);

CREATE TABLE IF NOT EXISTS media_resources (
    id TEXT PRIMARY KEY,
    source_media_id TEXT NOT NULL,
    derived_media_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (source_media_id) REFERENCES media_meta(id),
    FOREIGN KEY (derived_media_id) REFERENCES media_meta(id)
);
```

### Migration 0011 — Model Registry & Benchmark

```sql
CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    provider_model_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    version TEXT,
    family TEXT,
    media_types TEXT NOT NULL DEFAULT '["image"]',
    capabilities TEXT NOT NULL DEFAULT '{}',
    default_params TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'active',
    cost_per_unit REAL,
    cost_unit TEXT,
    metadata TEXT DEFAULT '{}',
    registered_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(provider, provider_model_id)
);

CREATE INDEX idx_models_provider ON models(provider);
CREATE INDEX idx_models_status ON models(status);
CREATE INDEX idx_models_family ON models(family);

CREATE TABLE IF NOT EXISTS model_tags (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(model_id, tag)
);

CREATE INDEX idx_model_tags_tag ON model_tags(tag);

CREATE TABLE IF NOT EXISTS benchmark_suites (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    prompts TEXT NOT NULL,
    media_type TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS benchmark_runs (
    id TEXT PRIMARY KEY,
    suite_id TEXT REFERENCES benchmark_suites(id),
    model_id TEXT NOT NULL REFERENCES models(id),
    prompt TEXT NOT NULL,
    prompt_index INTEGER,
    media_type TEXT NOT NULL,
    provider_latency_ms INTEGER,
    total_duration_ms INTEGER,
    file_size_bytes INTEGER,
    quality_score_auto REAL,
    quality_score_human REAL,
    cost_cents REAL,
    seed INTEGER,
    output_storage_key TEXT,
    content_type TEXT,
    width INTEGER,
    height INTEGER,
    duration_ms INTEGER,
    error TEXT,
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_benchmark_runs_model ON benchmark_runs(model_id);
CREATE INDEX idx_benchmark_runs_suite ON benchmark_runs(suite_id);
CREATE INDEX idx_benchmark_runs_media ON benchmark_runs(media_type);
```

---

## 6. Complete File Manifest (24 files)

### New Files (17)

| # | File | Purpose |
|---|------|---------|
| 1 | `toll/ports/media.py` | `MediaPort`, `MediaRequest`, `MediaResult` |
| 2 | `toll/ports/media_storage.py` | `MediaStorage` abstract (save, get_path, delete) |
| 3 | `toll/ports/model_registry.py` | `Model` dataclass |
| 4 | `toll/ports/benchmark.py` | `BenchmarkRun`, `BenchmarkSuite` dataclasses |
| 5 | `toll/adapters/media/__init__.py` | Package init |
| 6 | `toll/adapters/media/fs_storage.py` | `FsMediaStorage` — filesystem save/retrieve |
| 7 | `toll/adapters/media/replicate.py` | `ReplicateMediaAdapter` — image generation |
| 8 | `toll/adapters/media/ollama.py` | `OllamaMediaAdapter` — stub for local models |
| 9 | `toll/application/media_service.py` | `MediaService` — generate image/video, create artifact |
| 10 | `toll/engine/renderers/media_renderer.py` | `MediaPreviewRenderer` — image/video HTML previews |
| 11 | `toll/model/migrations/0010_media.sql` | `media_meta` + `media_resources` tables |
| 12 | `toll/model/migrations/0011_model_registry.sql` | `models` + `model_tags` + `benchmark_suites` + `benchmark_runs` tables |
| 13 | `toll/model_registry/__init__.py` | Package init |
| 14 | `toll/model_registry/service.py` | `ModelRegistryService` — register, list, query, find_best |
| 15 | `toll/model_registry/repository.py` | `ModelRepository` — SQL CRUD with filtering |
| 16 | `toll/model_registry/seed.py` | Seed data: Flux Schnell, Flux Pro, SDXL, DALL-E 3 |
| 17 | `toll/benchmark/__init__.py` | Package init |
| 18 | `toll/benchmark/service.py` | `BenchmarkService` — run, compare, leaderboard, suite mgmt |
| 19 | `toll/benchmark/repository.py` | `BenchmarkRepository` — SQL CRUD + aggregation |
| 20 | `toll/benchmark/runner.py` | `BenchmarkRunner` — orchestrate generation + measure |
| 21 | `toll/benchmark/quality_scorer.py` | `QualityScorer` — AI-based quality evaluation |

### Modified Files (7)

| # | File | Change |
|---|------|--------|
| 22 | `toll/model/artifact.py` | Add `IMAGE_GEN`, `VIDEO` to `ArtifactType` enum |
| 23 | `toll/core/feature_flags.py` | Register 8 flags: 2 media + 4 registry + 2 benchmark |
| 24 | `toll/core/provider_selector.py` | Add benchmark-aware `select()` with fallback to static scores |
| 25 | `toll/application/handler_registry.py` | Register `media_generate`, `model_register`, `model_list`, `benchmark_run`, `benchmark_compare` handlers |
| 26 | `toll/engine/renderers/preview_renderer.py` | Add `image_gen_preview()`, `video_preview()`, update `_summarize` |
| 27 | `web/index.html` | New sidebar navigation; ZUNO views; Models + Lab view placeholders |

---

## 7. Feature Flags

```python
# Media Layer — Sprint 6A
"media_generation": True,         # master switch for media generation
"media_image": True,              # image generation (sub-switch)
"media_video": False,             # video generation (opt-in, heavier)
"media_local_storage": True,      # filesystem media storage

# Model Registry — Sprint 6A
"model_registry": True,           # model registry subsystem
"model_registry_seed": True,      # auto-seed known models on init

# Benchmark Lab — Sprint 6A
"benchmark_lab": False,           # benchmark subsystem (power-user feature)
"benchmark_auto_quality": False,  # AI quality scoring (token cost)
```

---

## 8. ProviderSelector Changes

### Current (`toll/core/provider_selector.py`)

```python
def _quality_score(self, provider: str) -> float:
    scores: dict[str, float] = {"opencode": 0.9, "ollama": 0.5}
    return scores.get(provider, 0.3)
```

### Updated Design

```python
class ProviderSelector:
    def __init__(self, registry, settings, flags, model_registry=None, benchmark_service=None):
        self.registry = registry
        self.settings = settings
        self.flags = flags
        self.model_registry = model_registry
        self.benchmark_service = benchmark_service

    def select(self, task_type: ArtifactType, prefer: str | None = None) -> str | None:
        # Phase 1: Use registry for available models
        # Phase 2: Use benchmark data for scoring
        # Fallback: Static quality scores

    def select_model(self, media_type: str, prefer_speed: bool = False,
                     prefer_quality: bool = False) -> str | None:
        """Select best model for a media generation task.
        
        Phase 1: Returns any active model for the media type.
        Phase 2: Queries benchmark aggregates for data-driven selection.
        """
        if self.benchmark_service and self.flags.is_enabled("benchmark_lab"):
            best = self.benchmark_service.get_best(media_type, prefer_speed, prefer_quality)
            if best:
                return best.model_id
        # Fallback: first active model from registry
        models = self.model_registry.list(media_type=media_type, status="active")
        return models[0].id if models else None
```

---

## 9. API Endpoints

### Media
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/media/generate` | Generate image/video from plan |
| `GET` | `/api/media/{id}` | Get media metadata |
| `GET` | `/api/media/{id}/file` | Serve media file bytes |

### Models
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/models` | List models (filterable) |
| `GET` | `/api/models/{id}` | Get model detail |
| `POST` | `/api/models/register` | Register new model |
| `PUT` | `/api/models/{id}` | Update model |
| `DELETE` | `/api/models/{id}` | Disable model |
| `GET` | `/api/models/providers` | List distinct providers |

### Benchmark
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/benchmarks/runs` | List runs |
| `POST` | `/api/benchmarks/run` | Run one-off benchmark |
| `GET` | `/api/benchmarks/suites` | List suites |
| `POST` | `/api/benchmarks/suites` | Create suite |
| `POST` | `/api/benchmarks/suites/{id}/run` | Execute suite across models |
| `GET` | `/api/benchmarks/compare` | Compare models |
| `GET` | `/api/benchmarks/leaderboard` | Ranked models |

---

## 10. Seed Data

On first init, `ModelRegistryService._seed()` populates:

| Provider | Model ID | Name | Media Types | Status |
|----------|----------|------|-------------|--------|
| replicate | black-forest-labs/flux-schnell | Flux Schnell | image | active |
| replicate | black-forest-labs/flux-pro | Flux Pro | image | active |
| replicate | stability-ai/sdxl | SDXL | image | active |
| openai | dall-e-3 | DALL-E 3 | image | coming_soon |

Users can add models from any future provider via the Register API or Models UI.

---

## 11. Implementation Phases

### Phase 1 — Storage & Schema (Foundation)
- Migrations 0010 + 0011
- `FsMediaStorage`
- `Model` / `BenchmarkRun` dataclasses
- `ArtifactType` enum update
- Feature flags registered
- Tests: 8

### Phase 2 — Model Registry
- `ModelRegistryService` + `ModelRepository`
- Seed data
- Registry API endpoints
- Tests: 8

### Phase 3 — Media Layer
- `MediaPort` + `MediaRequest` / `MediaResult`
- `ReplicateMediaAdapter`
- `MediaService` (image + video generation)
- Media + Preview renderers
- `ProviderSelector` refactor
- Handler registration
- Tests: 10

### Phase 4 — Benchmark Lab
- `BenchmarkService` + `BenchmarkRepository`
- `BenchmarkRunner` + `QualityScorer`
- Benchmark API endpoints
- Tests: 8

### Phase 5 — ZUNO Navigation & UI
- Sidebar restructure with nav items
- View switching (JS + CSS)
- Models view (catalog table + register form)
- Lab view (suite list + comparison dashboard)
- Remaining API wiring
- Tests: 4 (E2E)

---

## 12. Test Plan (38 tests)

| Area | Count | Key Tests |
|------|-------|-----------|
| Storage (media) | 4 | save, get_path, delete, large file rejection |
| Ports (dataclasses) | 4 | `MediaRequest`, `MediaResult`, `Model`, `BenchmarkRun` defaults |
| Model Registry | 8 | register, duplicate reject, get, list filters, disable, find_best, seed |
| Media Service | 6 | image gen, video gen, missing model, provider unavailable, flag gating |
| Benchmark | 8 | run_single, run_suite, compare, leaderboard, quality scorer, error handling |
| Replicate adapter | 4 | model mapping, generate success, timeout, unsupported type |
| ProviderSelector | 2 | registry-aware select, fallback behavior |
| API integration | 2 | full pipeline (plan→media→artifact), benchmark round-trip |

---

## 13. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Replicate API changes mid-sprint | High | Adapter isolates to one file; tests mock the network layer |
| ZUNO nav restructure breaks chat | High | Chat view is untouched HTML; new nav is additive above it |
| Model registry DB grows stale | Medium | Seed + manual registration covers both paths |
| Benchmark costs add up | Low | Gated behind `benchmark_lab: False`; user must opt in |
| Video generation is slow | Medium | Timeout per adapter; consider async in future sprint |

---

## 14. Design Docs Superseded

| Doc | Status |
|-----|--------|
| `docs/sprint-6-media-layer-design.md` | Superseded by this plan |
| `docs/sprint-6a-model-registry-benchmark-design.md` | Superseded by this plan |
| `docs/sprint-6a-execution-plan.md` | **Active** — use for implementation |
