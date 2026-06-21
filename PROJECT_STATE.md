# TOOL Project State

## Project Overview

- **Mission**: توحيد — unified personal AI assistant for content creation, research, and workflow automation
- **Current Version**: `1.0.0`
- **Current Git Tags**: `v0.4-artifact-system` (Sprint 4), `v0.5-research-foundation` (Sprint 5A), `v0.5.1-research-memory` (Sprint 5C), `v0.6.0-notebooklm` (Sprint 5B)

## Completed Sprints

### Sprint 0 — Foundation

- **Goal**: Project scaffolding, port/adapter pattern, SQLite persistence, AI provider integration
- **Key Deliverables**:
  - `toll/ports/` — ABCs for LLM, Search, Settings, Repository
  - `toll/adapters/llm/` — OpenCodeProvider and OllamaProvider implementations
  - `toll/adapters/search/` — DuckDuckGoSearch (Lite HTML scraping, no API key)
  - `toll/core/` — Storage, Settings, Config, FeatureFlags, Registry
  - `toll/engine/` — ContentMachine, PromptGenerator, Reports (legacy)
  - `api/main.py` — FastAPI entry point
  - `api/routers/engine.py` — `/api/chat`, `/api/content`, `/api/prompt`, `/api/report`, `/api/present`, `/api/status`
  - `api/routers/config.py` — `/api/config`, `/api/flags`
  - Database migrations: `0001_initial.sql` (usage, config, history)
  - CLI and Telegram bot interfaces
  - `web/` — SPA dashboard

- **Status**: Complete

### Sprint 1 — Core Enhancements

- **Goal**: Rate limiting, conversation store, provider selection
- **Key Deliverables**:
  - `toll/core/limiter.py` — Daily rate limiter per provider
  - `toll/core/conversations.py` — ConversationStore with CRUD
  - `toll/core/provider_selector.py` — ProviderSelector with round-robin and fallback
  - `api/routers/conversations.py` — Conversation API endpoints

- **Status**: Complete

### Sprint 2 — Memory Graph, Workspace Manager, Server-Side Conversations

- **Goal**: Structured memory, workspace context, persistent conversations
- **Key Deliverables**:
  - `toll/memory/graph.py` — MemoryGraph with 5 types (global, brand, university, project, knowledge), importance scoring, recency tracking, feedback learning
  - `toll/workspace/manager.py` — WorkspaceManager with 3 types (brand, university, project), semester support, active state tracking
  - `toll/core/connection_manager.py` — Thread-safe SQLite connection manager with WAL mode
  - `toll/model/migrations/0002_memory_graph.sql` — memories, workspaces, semesters, workspace_state, conversations, messages tables
  - `api/routers/workspaces.py` — Workspace and semester API endpoints
  - Enhanced conversations API with workspace filtering

- **Status**: Complete

### Sprint 3 — Context Engine, Planner, and Workflow Engine

- **Goal**: Intent classification, workflow execution, context-aware retrieval
- **Key Deliverables**:
  - `toll/context/engine.py` — ContextEngine with workspace-aware retrieval, parent-following, tiered importance scoring
  - `toll/planner/planner.py` — Planner with intent classification (23 intents), approval matrix (auto/approval/blocked), keyword matching (Arabic + English), 3 modes (strict/balanced/fast)
  - `toll/workflow/engine.py` — WorkflowEngine with handler registration, step execution, approval gating, status tracking
  - `toll/application/handler_registry.py` — Handler registration for carousel, report, presentation, search, code, prompt, chat
  - `toll/application/carousel_service.py`, `report_service.py`, `presentation_service.py` — Artifact-generating service handlers
  - `toll/engine/prompt_gen.py` — PromptGenerator with context injection
  - `toll/model/migrations/0003_workflows.sql` — workflows table
  - `api/routers/planner.py` — Plan and workflow API endpoints

- **Status**: Complete

### Sprint 3.5 — Open Design Integration

- **Goal**: Push artifacts to Open Design preview platform
- **Key Deliverables**:
  - `toll/application/opendesign_service.py` — OpenDesignService (CLI-based push via `opendesign create`)
  - `toll/core/settings.py` — Settings system with env var > SQLite > defaults precedence
  - Enhanced preview renderer with Open Design preview links
  - Handler registration for `opendesign_push`

- **Status**: Complete

### Sprint 4 — Artifact System

- **Goal**: Full artifact lifecycle management, renderers, archive/restore
- **Key Deliverables**:
  - `toll/model/artifact.py` — Artifact model, ArtifactType enum (10 types), ArtifactStatus enum, ArtifactRepository
  - `toll/application/artifact_service.py` — ArtifactService with create/update/archive/restore, file I/O for rendered outputs
  - `toll/engine/renderers/` — 6 renderers:
    - `base.py` — BaseRenderer ABC
    - `carousel_renderer.py` — Interactive carousel HTML (dark theme, dot navigation)
    - `report_renderer.py` — Formal report HTML (serif, academic styling)
    - `presentation_renderer.py` — Full-screen presentation HTML (slide transitions)
    - `code_renderer.py` — Code snippet HTML (syntax-highlighting-friendly)
    - `preview_renderer.py` — Preview HTML per type (carousel, report, presentation, code, generic, research) + JSON preview
  - `toll/model/migrations/0004_artifacts.sql` — artifacts table with FK to workflows, indexing on type/status/workspace
  - `api/routers/artifacts.py` — Artifact API (list, get, render, preview, delete)
  - Archive support (tar.gz with metadata)
  - 127 tests passing

- **Status**: Complete

### Sprint 5A — Research Foundation

- **Goal**: Academic research capabilities — source management, citation formatting, deduplication, multiple providers
- **Key Deliverables**:
  - `toll/ports/research.py` — ResearchProvider ABC (search, search_by_ids, cite, synthesize, rate_limit)
  - `toll/ports/research_source.py` — ResearchSource (18 fields), ResearchQuery, ResearchResult, SourceType/CitationStyle/AccessType enums
  - `toll/research/web_researcher.py` — WebResearcher (DuckDuckGo-based fallback, no API key needed)
  - `toll/research/source_manager.py` — SourceManager (collect, store, retrieve, list, tag, delete, weighted ranking, BibTeX/RIS import)
  - `toll/research/dedup.py` — DedupEngine (4 strategies: DOI 1.0, URL 1.0, title Levenshtein 0.85, author+year 0.95; Union-Find merge, DB logging)
  - `toll/research/citation_engine.py` — CitationEngine (APA, MLA, IEEE, Chicago Notes, Chicago Author-Date, Vancouver; BibTeX export, RIS export)
  - `toll/application/research_service.py` — ResearchService with 3 modes (standard/quick/deep), AI synthesis, key findings extraction
  - `toll/adapters/research/google_drive.py` — GoogleDriveAdapter Phase 1 (local backup only, gated by `google_drive_backup` flag)
  - `toll/model/migrations/0005_research.sql` — research_sources, research_citations, research_dedup_log tables + 7 indexes
  - PreviewRenderer `research_preview()` — RTL Arabic research preview HTML
  - 10 research feature flags + `google_drive_backup`
  - `api/routers/research.py` — Research API (POST /api/research, GET /api/research/styles, GET /api/research/modes)
  - 43 new tests, 170 total passing

- **Status**: Complete

### Sprint 5B — NotebookLM Integration

- **Goal**: NotebookLM-style research notebooks — source management, notes, snapshots, audio overviews
- **Key Deliverables**:
  - `toll/ports/notebook.py` — NotebookPort ABC (upload_source, create_notes, query, list_sources, delete_source, create_snapshot, list/get/delete snapshots, generate_audio_overview)
  - `toll/adapters/notebooks/notebooklm.py` — NotebookLMProvider implementation
  - `toll/application/notebook_service.py` — NotebookService with full lifecycle
  - `toll/model/migrations/0007_notebook_source_content.sql`, `0008_drop_notebook_fts.sql`, `0009_research_memory.sql`
  - `api/routers/notebooks.py` — full Notebook API (17 endpoints)
  - 34 new tests
  - Tag: `v0.6.0-notebooklm`

- **Status**: Complete

### Sprint 5C — Research Memory Automation

- **Goal**: Automated research memory — importance scoring, auto-indexing, knowledge vault, context-aware retrieval
- **Key Deliverables**:
  - `toll/research/importance.py` — ImportanceScorer with learned weights
  - `toll/research/memory_service.py` — MemoryService with auto-indexing and context retrieval
  - Research memory feature flags: `research_memory_auto_index`, `research_memory_context`, `research_memory_importance_learn`, `research_memory_knowledge_vault`
  - Notebook port made synchronous with content field
  - Notebook handlers refactored to lambda wrappers
  - 34 new tests
  - Tag: `v0.5.1-research-memory`

- **Status**: Complete

### Sprint 6A — Media Foundation + Model Registry + Benchmark Lab

- **Goal**: Image generation infrastructure, model registry, and benchmarking capability
- **Key Deliverables**:
  - **Media Layer** — `MediaService`, `ReplicateMediaAdapter`, `OllamaMediaAdapter`, `FsMediaStorage`, `MediaPreviewRenderer`
  - **Model Registry** — `ModelRegistryService`, `ModelRepository`, seed data (4 models: flux-schnell, flux-pro, sdxl, dall-e-3)
  - **Benchmark Lab** — `BenchmarkService`, `BenchmarkRepository`, `BenchmarkRunner`, `QualityScorer` (weighted: no_error 0.5, latency 0.3, file_size 0.2)
  - **API** — `/api/models` (5 endpoints), `/api/benchmark` (7 endpoints)
  - **Migrations** — `0010_media.sql` (media_meta, media_resources), `0011_model_registry.sql` (models, model_tags, benchmark_suites, benchmark_runs — 5 tables + 8 indexes)
  - **Feature flags** (8 new): `media_generation`, `media_image`, `media_video` (default F), `media_local_storage`, `model_registry`, `model_registry_seed`, `benchmark_lab` (default F), `benchmark_auto_quality` (default F)
  - **Handler registrations**: `media_generate`, `benchmark_run`, `benchmark_create_suite`, `benchmark_list_suites`, `benchmark_model_scores`
  - **UI** — ZUNO sidebar navigation (Chat/Notebooks/Models/Lab), Models view, Lab view with suite creation and run
  - 108 new tests (Phases 1-5), 352 total passing
  - 17 new files, 7 modified files

- **Status**: Complete (tagged `v0.6-media-foundation`)

## Current Architecture

### Core Layer
- **toll/core/** — Config, Storage, Settings, FeatureFlags, ConnectionManager, RateLimiter, ConversationStore, ProviderRegistry, ProviderSelector
- **toll/ports/** — ABCs for LLM, Search, Research, Settings, Repository
- **api/** — FastAPI application with 7 routers
- **cli/** — CLI entry point
- **bot/** — Telegram bot

### Memory Layer
- **toll/memory/** — MemoryGraph with 5 types (global, brand, university, project, knowledge), importance scoring (1-10), recency/importance context retrieval, feedback learning

### Workflow Layer
- **toll/planner/** — Planner with 25 intents, approval matrix, keyword matching (Arabic + English), 3 modes
- **toll/workflow/** — WorkflowEngine with handler registration, approval gating, status state machine
- **toll/application/** — Service handlers for each intent (carousel, report, presentation, research, opendesign, artifact)

### Artifact Layer
- **toll/model/artifact.py** — Artifact model with repository (CRUD, archive/restore, file I/O)
- **toll/engine/renderers/** — 8 renderers (carousel, report, presentation, code, preview, research preview, image_preview, video_preview)
- **toll/application/artifact_service.py** — Full lifecycle management

### Research Layer
- **toll/ports/research.py**, **toll/ports/research_source.py** — Provider ABC and data model
- **toll/research/** — WebResearcher, SourceManager, DedupEngine, CitationEngine, ImportanceScorer, MemoryService
- **toll/adapters/research/** — GoogleDriveAdapter (Phase 1: local backup)
- **toll/application/research_service.py** — 3-mode workflow handler

### Notebook Layer
- **toll/ports/notebook.py** — NotebookPort ABC
- **toll/adapters/notebooks/notebooklm.py** — NotebookLMProvider
- **toll/application/notebook_service.py** — NotebookService

### Media Layer
- **toll/ports/media.py** — MediaPort ABC, MediaRequest, MediaResult dataclasses
- **toll/ports/media_storage.py** — MediaStorage ABC
- **toll/adapters/media/** — ReplicateMediaAdapter (image gen), OllamaMediaAdapter (stub), FsMediaStorage
- **toll/application/media_service.py** — MediaService with provider resolution and artifact storage
- **toll/engine/renderers/media_renderer.py** — MediaPreviewRenderer (image_preview, video_preview HTML)

### Model Registry
- **toll/ports/model_registry.py** — Model dataclass
- **toll/model_registry/** — ModelRegistryService, ModelRepository (CRUD, filtering, tagging), seed data (4 models)

### Benchmark Lab
- **toll/ports/benchmark.py** — BenchmarkRun, BenchmarkSuite dataclasses
- **toll/benchmark/** — BenchmarkService, BenchmarkRepository, BenchmarkRunner, QualityScorer (weighted criteria)

## Current Directory Structure

```
تول/
├── api/
│   ├── main.py
│   ├── dependencies.py
│   └── routers/
│       ├── engine.py          # Chat, content, report, present, status
│       ├── config.py          # Config, feature flags
│       ├── workspaces.py      # Workspace CRUD, semester management
│       ├── conversations.py   # Conversation CRUD
│       ├── planner.py         # Plan, workflow management
│       ├── artifacts.py       # Artifact CRUD, render, preview
│       ├── research.py        # Research, citation styles, modes
│       ├── notebooks.py       # Notebook CRUD, sources, notes, snapshots
│       ├── models.py          # Model Registry CRUD
│       └── benchmark.py       # Benchmark suites, runs, scores
├── bot/
│   └── telegram.py
├── cli/
│   └── main.py
├── data/
│   ├── artifacts/
│   └── toll.db
├── docs/
│   ├── sprint-reports/
│   ├── sprint4-report.md
│   ├── sprint5a-report.md
│   ├── sprint-5b.2-fixes-report.md
│   ├── sprint-5c-research-memory-design.md
│   ├── sprint-6-media-layer-design.md
│   ├── sprint-6a-execution-plan.md
│   ├── sprint-6a-model-registry-benchmark-design.md
│   └── v0.6-architecture-audit.md
├── tests/
│   ├── adapters/
│   │   ├── test_duckduckgo.py
│   │   ├── test_fs_storage.py
│   │   ├── test_ollama_adapter.py
│   │   └── test_replicate_adapter.py
│   ├── api/
│   │   ├── test_artifacts_api.py
│   │   ├── test_benchmark_api.py
│   │   ├── test_models_api.py
│   │   ├── test_notebooks_api.py
│   │   ├── test_research_memory_api.py
│   │   └── test_research_api.py
│   ├── application/
│   │   ├── test_carousel_service.py
│   │   ├── test_handler_registry.py
│   │   ├── test_media_service.py
│   │   ├── test_notebook_service.py
│   │   └── test_report_service.py
│   ├── benchmark/
│   │   ├── test_quality_scorer.py
│   │   ├── test_repository.py
│   │   ├── test_runner.py
│   │   └── test_service.py
│   ├── core/
│   ├── engine/
│   │   └── renderers/
│   │       └── test_media_renderer.py
│   ├── model_registry/
│   │   ├── test_repository.py
│   │   └── test_service.py
│   ├── ports/
│   │   ├── test_benchmark.py
│   │   ├── test_media.py
│   │   └── test_model_registry.py
│   └── research/
│       ├── test_importance.py
│       ├── test_memory_service.py
│       ├── test_source_manager.py
│       └── test_web_researcher.py
├── toll/
│   ├── adapters/
│   │   ├── llm/               # OpenCodeProvider, OllamaProvider
│   │   ├── media/             # ReplicateMediaAdapter, OllamaMediaAdapter, FsMediaStorage
│   │   ├── notebooks/         # NotebookLMProvider
│   │   ├── research/          # GoogleDriveAdapter
│   │   └── search/            # DuckDuckGoSearch
│   ├── application/           # Service handlers (+ MediaService)
│   ├── benchmark/             # BenchmarkService, Repository, Runner, QualityScorer
│   ├── context/               # ContextEngine
│   ├── core/                  # Config, Storage, Settings, Flags, etc.
│   ├── engine/
│   │   └── renderers/         # 8 HTML renderers (+ media_renderer)
│   ├── memory/                # MemoryGraph
│   ├── model/
│   │   └── migrations/        # 11 migration files
│   ├── model_registry/        # ModelRegistryService, Repository, Seed
│   ├── planner/               # Planner
│   ├── ports/                 # ABCs (+ Media, MediaStorage, Benchmark, Model)
│   ├── research/              # WebResearcher, SourceManager, DedupEngine, CitationEngine, ImportanceScorer, MemoryService
│   ├── workflow/              # WorkflowEngine
│   └── workspace/             # WorkspaceManager
└── web/
    ├── index.html
    ├── manifest.json
    └── sw.js
```

## Feature Flags

### Core Layer (enabled by default)
| Flag | Default |
|------|---------|
| `core_chat` | `True` |
| `provider_opencode` | `True` |
| `provider_ollama` | `True` |
| `rate_limiting` | `True` |
| `web_dashboard` | `True` |
| `cli_enabled` | `True` |
| `artifact_basic` | `True` |
| `settings_system` | `True` |
| `planner_enabled` | `True` |
| `workflow_enabled` | `True` |
| `memory_graph` | `True` |
| `workspace_manager` | `True` |
| `context_engine` | `True` |
| `artifact_system` | `True` |
| `carousel_engine` | `True` |
| `report_engine` | `True` |
| `presentation_engine` | `True` |

### Core Layer (disabled by default)
| Flag | Default |
|------|---------|
| `memory_auto_learning` | `False` |
| `planner_strict_mode` | `False` |
| `planner_fast_mode` | `False` |

### Layer 2 — Dormant
| Flag | Default |
|------|---------|
| `preference_memory` | `False` |
| `knowledge_vault` | `False` |
| `google_drive_sync` | `False` |
| `telegram_enabled` | `False` |
| `task_journal` | `False` |
| `health_dashboard` | `False` |
| `self_improvement` | `False` |
| `users_enabled` | `False` |
| `opendesign_integration` | `False` |

### Research Layer — Sprint 5A
| Flag | Default |
|------|---------|
| `research_provider` | `True` |
| `research_deep` | `False` |
| `citation_engine` | `True` |
| `source_dedup` | `True` |
| `source_import` | `False` |
| `google_drive_backup` | `False` |
| `provider_semantic_scholar` | `False` |
| `provider_google_scholar` | `False` |
| `provider_arxiv` | `False` |
| `provider_crossref` | `False` |
| `provider_zotero` | `False` |

### Sprint 5B — NotebookLM Integration
| Flag | Default |
|------|---------|
| `notebooklm_enabled` | `True` |
| `notebooklm_memory_index` | `True` |
| `notebooklm_artifact_create` | `True` |
| `notebooklm_strict_local` | `False` |
| `notebooklm_snapshots` | `True` |
| `notebooklm_audio_overview` | `False` |

### Sprint 5C — Research Memory
| Flag | Default |
|------|---------|
| `research_memory_auto_index` | `True` |
| `research_memory_context` | `False` |
| `research_memory_importance_learn` | `True` |
| `research_memory_knowledge_vault` | `True` |

### Sprint 6A — Media Foundation
| Flag | Default |
|------|---------|
| `media_generation` | `True` |
| `media_image` | `True` |
| `media_video` | `False` |
| `media_local_storage` | `True` |
| `model_registry` | `True` |
| `model_registry_seed` | `True` |
| `benchmark_lab` | `False` |
| `benchmark_auto_quality` | `False` |

## Providers

### LLM Providers
| Provider | File | Status |
|----------|------|--------|
| OpenCode | `toll/adapters/llm/opencode.py` | **Implemented** — subprocess to `opencode run` |
| Ollama | `toll/adapters/llm/ollama.py` | **Implemented** — subprocess to `ollama run` |

### Search Providers
| Provider | File | Status |
|----------|------|--------|
| DuckDuckGo | `toll/adapters/search/duckduckgo.py` | **Implemented** — Lite HTML scrape, no API key |

### Research Providers
| Provider | File | Status |
|----------|------|--------|
| WebResearcher (DDG) | `toll/research/web_researcher.py` | **Implemented** — wraps DuckDuckGoSearch into ResearchProvider ABC |
| Semantic Scholar | — | **Planned** (flag: `provider_semantic_scholar`, default `False`) |
| Google Scholar | — | **Planned** (flag: `provider_google_scholar`, default `False`) |
| arXiv | — | **Planned** (flag: `provider_arxiv`, default `False`) |
| Crossref | — | **Planned** (flag: `provider_crossref`, default `False`) |
| Zotero | — | **Planned** (flag: `provider_zotero`, default `False`) |

### Design Providers
| Provider | Status |
|----------|--------|
| Open Design | **Implemented** (gated by `opendesign_integration`, default `False`) — pushes artifacts via `opendesign create` CLI |

### Media Providers
| Provider | File | Status |
|----------|------|--------|
| Replicate | `toll/adapters/media/replicate.py` | **Implemented** — image generation via Replicate API (requires API token; `replicate` package) |
| Ollama | `toll/adapters/media/ollama.py` | **Stub** — returns "not yet supported" |

### Model Registry Providers
| Provider | Seed Model |
|----------|-----------|
| Replicate | `replicate:flux-schnell` (active), `replicate:flux-pro` (active), `replicate:sdxl` (active) |
| OpenAI | `openai:dall-e-3` (coming_soon) |

## Database

### Current Migrations
| File | Tables Created |
|------|----------------|
| `0001_initial.sql` | `usage`, `config`, `history` |
| `0002_memory_graph.sql` | `memories`, `workspaces`, `semesters`, `workspace_state`, `conversations`, `messages` |
| `0003_workflows.sql` | `workflows` |
| `0004_artifacts.sql` | `artifacts` |
| `0005_research.sql` | `research_sources`, `research_citations`, `research_dedup_log` |
| `0006_notebooks.sql` | `notebooks` |
| `0007_notebook_source_content.sql` | `notebook_source_content` |
| `0008_drop_notebook_fts.sql` | Drops FTS virtual table |
| `0009_research_memory.sql` | Research memory tables |
| `0010_media.sql` | `media_meta`, `media_resources` |
| `0011_model_registry.sql` | `models`, `model_tags`, `benchmark_suites`, `benchmark_runs` |

### Current Major Tables (26 total)
- **System**: `usage`, `config`, `history`, `migrations`
- **Memory**: `memories`
- **Workspace**: `workspaces`, `semesters`, `workspace_state`
- **Conversation**: `conversations`, `messages`
- **Workflow**: `workflows`
- **Artifact**: `artifacts`
- **Media**: `media_meta`, `media_resources`
- **Model Registry**: `models`, `model_tags`
- **Benchmark**: `benchmark_suites`, `benchmark_runs`
- **Notebook**: `notebooks`, `notebook_source_content`
- **Research Memory**: research memory tables
- **Research**: `research_sources`, `research_citations`, `research_dedup_log`

## API Surface

### Engine Router (`/api`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat` | Main chat — intent classification, artifact generation, fallback conversation |
| POST | `/content` | Legacy content generation (carousel + social post) |
| POST | `/prompt` | Generate prompt template |
| POST | `/report` | Generate report |
| POST | `/present` | Generate presentation |
| GET | `/status` | AI limit + provider status |

### Config Router (`/api`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/config` | Get all settings |
| POST | `/config/{key}/{value}` | Set a config value |
| GET | `/flags` | Get all feature flags |
| POST | `/flags/{name}/{enabled}` | Enable/disable a flag |

### Workspaces Router (`/api`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/workspaces` | List workspaces (optional type filter) |
| POST | `/workspaces` | Create workspace (brand/university/project) |
| DELETE | `/workspaces/{id}` | Delete workspace (returns 501 — not implemented) |
| POST | `/semesters` | Create semester under university |
| GET | `/semesters/{university_id}` | List semesters for university |
| GET | `/workspace/active` | Get active workspace state |
| POST | `/workspace/active` | Set active workspace |
| DELETE | `/workspace/active` | Clear active workspace |

### Conversations Router (`/api`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/conversations` | List conversations (optional workspace filter) |
| POST | `/conversations` | Create conversation |
| GET | `/conversations/{id}` | Get conversation with messages |
| PUT | `/conversations/{id}/title` | Update title |
| DELETE | `/conversations/{id}` | Delete conversation |

### Planner Router (`/api`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/plan` | Classify intent, get approval level |
| GET | `/plan/mode` | Get planner mode |
| POST | `/plan/mode` | Set planner mode |
| POST | `/workflows` | Create + run workflow from plan |
| GET | `/workflows` | List workflows (optional status filter) |
| GET | `/workflows/{id}` | Get workflow |
| POST | `/workflows/{id}/approve` | Approve pending workflow |
| POST | `/workflows/{id}/reject` | Reject pending workflow |
| POST | `/workflows/{id}/run` | Run approved workflow |

### Artifacts Router (`/api`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/artifacts` | List artifacts (filters: type, status, workflow_id) |
| GET | `/artifacts/{id}` | Get artifact metadata |
| GET | `/artifacts/{id}/content` | Get JSON content |
| GET | `/artifacts/{id}/render` | Get rendered HTML |
| GET | `/artifacts/{id}/preview` | Get preview (HTML or JSON) |
| DELETE | `/artifacts/{id}` | Soft-delete artifact |

### Research Router (`/api`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/research` | Create research artifact (modes: standard/quick/deep) |
| GET | `/research/styles` | List supported citation styles |
| GET | `/research/modes` | List research modes |

## Workspace System

- **Brand** — Brand workspace, stores brand-specific context and memories
- **University** — University workspace with semester sub-division
- **Project** — Project workspace for general project management
- **Semester** — Sub-unit of university workspaces, each with its own metadata

Active state tracks one of each type per user (default user: `"default"`). Context engine uses active state for workspace-aware memory retrieval.

## Memory System

- **Global** — Cross-workspace general memories (no entity_id)
- **Brand** — Brand-specific memories (entity_id = brand_id)
- **University** — University-specific memories (entity_id = university_id)
- **Project** — Project-specific memories (entity_id = project_id)
- **Knowledge** — Knowledge vault (entity_id optional, for persistent reference data)

Memories scored by importance (1-10) with recency tracking. Context retrieval weights by importance × recency decay. Feedback learning adjusts importance automatically.

## Artifact System

Supported artifact types:
- `carousel` — Interactive slide carousel (dark theme, dot navigation)
- `report` — Formal academic-style report (serif, section/subsection)
- `presentation` — Full-screen presentation (slide transitions, controls)
- `code` — Syntax-highlighted code snippet
- `search_result` — Raw search results
- `prompt` — Generated prompts
- `social_post` — Social media post content
- `research` — Research paper with sources, citations, synthesis
- `image` — Image artifacts (placeholder)
- `generic` — Generic content artifact

Each artifact supports: creation, rendering (HTML), preview, archive (tar.gz), soft-delete, workspace association, workflow association.

## Research System

### Implemented Features
- **Web search** via DuckDuckGo (no API key, Arabic-friendly)
- **Source management** — store, retrieve, list by artifact, tag, delete, weighted ranking
- **Deduplication** — DOI (1.0) → URL (1.0) → title Levenshtein (0.85) → author+year (0.95), Union-Find merge
- **Citation formatting** — APA 7th, MLA 9th, IEEE, Chicago Notes, Chicago Author-Date, Vancouver
- **Export** — BibTeX and RIS format export
- **Import** — BibTeX and RIS format import (gated by `source_import` flag)
- **AI synthesis** — Arabic synopsis generation via LLM, key findings extraction
- **3 research modes**: standard (full artifact), quick (sources only, no storage), deep (same as standard)
- **Google Drive backup Phase 1** — local file backup (gated by `google_drive_backup`)

### Planned Features
- **Semantic Scholar provider** — `provider_semantic_scholar` flag
- **Google Scholar provider** — `provider_google_scholar` flag
- **arXiv provider** — `provider_arxiv` flag
- **Crossref provider** — `provider_crossref` flag
- **Zotero provider** — `provider_zotero` flag
- **Google Drive real API integration** — true upload/download/sync (not Phase 1 local backup)
- **Video generation** — enable `media_video` flag with Veo/Runway adapter
- **Character consistency** — seed-based style preservation for media generation
- **Advanced benchmark automation** — scheduled runs, trend analysis, model comparison dashboard

## Release History

### v0.4-artifact-system

- **Git Tag**: `v0.4-artifact-system`
- **Commit**: `177cc5d`
- **Summary**:
  - Artifact System — full lifecycle management (create, render, preview, archive, delete)
  - Application Services — carousel, report, presentation, Open Design push
  - Renderers — 5 HTML renderers (carousel, report, presentation, code, preview)
  - Provider Selector — round-robin with fallback
  - Migration `0004_artifacts.sql` — artifacts table with FK to workflows
  - 127 tests passing

### v0.5-research-foundation

- **Git Tag**: `v0.5-research-foundation`
- **Commit**: `2eb5c77`
- **Summary**:
  - Research Layer Foundation — ResearchProvider ABC, data model, 3 research modes
  - Citation Engine — 6 styles (APA, MLA, IEEE, Chicago Notes, Chicago Date, Vancouver) + BibTeX/RIS export
  - Source Management — store, retrieve, list, tag, delete, weighted ranking, BibTeX/RIS import
  - Dedup Engine — 4 strategies (DOI, URL, title, author+year) with Union-Find merge
  - Research Artifacts — full research artifact with AI synthesis and key findings extraction
  - Research API — `POST /api/research`, `GET /api/research/styles`, `GET /api/research/modes`
  - Google Drive Phase 1 — local backup (gated)
  - Migration `0005_research.sql` — 3 tables + 7 indexes
  - 43 new tests, 170 total passing

### v0.5.1-research-memory

- **Git Tag**: `v0.5.1-research-memory`
- **Commit**: `5727af8`
- **Summary**:
  - Research Memory Automation — ImportanceScorer, MemoryService, knowledge vault
  - Notebook port made synchronous with content field
  - Notebook handlers refactored to lambda wrappers
  - Migrations 0007-0009: notebook source content, drop FTS, research memory tables
  - Feature flags: `research_memory_auto_index`, `research_memory_context`, `research_memory_importance_learn`, `research_memory_knowledge_vault`
  - 34 new tests, 244 total passing

### v0.6.0-notebooklm

- **Git Tag**: `v0.6.0-notebooklm`
- **Commit**: `994759b`
- **Summary**:
  - NotebookLM Integration — NotebookPort ABC, NotebookLM provider, NotebookService
  - Full Notebook API with 17 endpoints
  - Snapshots, notes, sources, audio overview support
  - Feature flags: `notebooklm_enabled`, `notebooklm_memory_index`, `notebooklm_artifact_create`, `notebooklm_strict_local`, `notebooklm_snapshots`, `notebooklm_audio_overview`
  - 34 new tests

### v0.6-media-foundation

- **Git Tag**: `v0.6-media-foundation`
- **Commit**: (current)
- **Summary**:
  - Media Layer — MediaService, ReplicateMediaAdapter, OllamaMediaAdapter, FsMediaStorage, MediaPreviewRenderer
  - Model Registry — ModelRegistryService, ModelRepository, seed data (4 models), CRUD API
  - Benchmark Lab — BenchmarkService, BenchmarkRepository, BenchmarkRunner, QualityScorer
  - API: `/api/models` (5 endpoints), `/api/benchmark` (7 endpoints)
  - Migrations 0010-0011: media_meta, media_resources, models, model_tags, benchmark_suites, benchmark_runs (6 tables + 8 indexes)
  - Feature flags (8 new): media_generation, media_image, media_video, media_local_storage, model_registry, model_registry_seed, benchmark_lab, benchmark_auto_quality
  - ZUNO UI: sidebar navigation (Chat/Notebooks/Models/Lab), Models view, Lab view
  - 108 new tests, 352 total passing

## Backup Locations

### GitHub

Repository: https://github.com/i5s/tool-ai-os

Protected Releases:

- `v0.4-artifact-system`
- `v0.5-research-foundation`
- `v0.5.1-research-memory`
- `v0.6.0-notebooklm`
- `v0.6-media-foundation`

### Local Database

- `data/toll.db` — SQLite database with WAL mode, contains all system/config/memory/workspace/conversation/workflow/artifact/research data

### Recommended Backup Strategy

1. GitHub Tags — source code snapshots
2. Database Backup — periodic copy of `data/toll.db`
3. Google Drive Archive — `data/drive_backup/` for artifact file backups (Phase 1, gated by `google_drive_backup` flag)

## Current Limitations

- No remote research providers beyond DuckDuckGo — Semantic Scholar, arXiv, Crossref, Google Scholar, Zotero are flag-gated but not implemented
- Google Drive integration is Phase 1 (local backup only) — no real API upload/download/sync
- `opendesign_integration` flag defaults to `False` — Open Design push requires manual enabling
- `DELETE /workspaces/{id}` returns 501 — workspace deletion is not implemented
- Telegram bot token is hardcoded (empty by default) — no env var or config support
- BrowserAI (`toll/core/browser.py`) is a placeholder — not implemented
- No user authentication or multi-user support
- Rate limiter uses daily counts — no per-user or per-endpoint granularity
- Research `deep` mode is functionally identical to standard mode
- No scheduled tasks or background job system
- Media generation limited to image via Replicate (no video/audio)
- Replicate adapter requires `replicate` Python package and API token to be available
- Benchmark Lab is opt-in only (`benchmark_lab` flag defaults to `False`)
- ProviderSelector does not consume benchmark data for model ranking — static scoring only
- No video adapter implemented (Veo, Runway, other video platforms)
- No character/style consistency between media generations
- No data export/import for workspace or memory data
- No integration tests for end-to-end workflows
- Test coverage does not include all API integration tests
- SQLite database — no migration path to PostgreSQL or other production DB

## Next Planned Sprint

### Sprint 6B — Media Layer 2 (Video & Audio)

- **Video adapter** — Veo, Runway, or MiniMax video generation via MediaPort (enable `media_video` flag)
- **Audio adapter** — TTS and audio processing (ElevenLabs, Kokoro)
- **Character consistency** — seed/face anchor preservation across generations
- **Benchmark-driven model selection** — `ProviderSelector.select()` consumes benchmark aggregates
- **Advanced benchmark dashboard** — trend charts, model comparison, automated quality gates
- **ZUNO Lab view enhancements** — run history, score history, side-by-side model comparison

## Future Roadmap

- **Sprint 6B** — Video & Audio adapters, character consistency, benchmark-driven selection
- **Sprint 7** — Advanced memory & knowledge graph (RAG pipeline, hybrid search, knowledge base import)
- **Sprint 8** — Production hardening (multi-user, PostgreSQL migration, proper auth)
