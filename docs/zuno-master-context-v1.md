# ZUNO (تول) — Master Context v1

> **Version**: 0.8.0-beta  
> **Tag**: v0.8b-operations-ui  
> **Commit**: 749e291  
> **Tests**: 453 passing  
> **Purpose**: Canonical project memory — bootstrap a new conversation with all final decisions.

---

## 1. Current Project Status

**Mission**: توحيد — unified personal AI assistant for content creation, research, and workflow automation.

**State**: Operations Layer active — usage tracking, storage management, cleanup system, provider dashboard operational. Prompt Intelligence Engine is production-integrated into all generation flows with active learning loop and context-aware prompt generation.

**Feature flag count**: 54 flags across 7 sprint groups.

---

## 2. Version & Release History

| Tag | Sprint | Description |
|-----|--------|-------------|
| v0.4-artifact-system | Sprint 4 | Artifact System — full lifecycle management |
| v0.5-research-foundation | Sprint 5A | Research Layer — citation engine, source management, dedup |
| v0.5.1-research-memory | Sprint 5C | Research Memory Automation — importance scoring, knowledge vault |
| v0.6.0-notebooklm | Sprint 5B | NotebookLM Integration — sources, notes, snapshots |
| v0.6-media-foundation | Sprint 6A | Media Layer + Model Registry + Benchmark Lab |
| v0.7a-prompt-intelligence-core | Sprint 7A | Prompt Intelligence Engine — profiles, execution profiles, templates |
| v0.7b-prompt-intelligence-integration | Sprint 7B | PIE wired into all 4 service flows + benchmark-aware ProviderSelector |
| v0.7c-prompt-learning-loop | Sprint 7C | Context integration fix, record_success/failure wired, score consumption |
| v0.8a-operations-layer | Sprint 8A | Usage Center, Storage Mgmt, Cleanup System, Provider Dashboard, Cost Monitoring |
| v0.8b-operations-ui | Sprint 8B | Operations UI panel — 5 tabs consuming all /api/operations endpoints |

---

## 3. Completed Sprints (6A → 8B)

### Sprint 6A — Media Foundation
- **Media Layer**: `MediaService`, `ReplicateMediaAdapter`, `FsMediaStorage`, `MediaPreviewRenderer`
- **Model Registry**: `ModelRegistryService`, `ModelRepository`, 4 seed models (flux-schnell, flux-pro, sdxl, dall-e-3)
- **Benchmark Lab**: `BenchmarkService`, `BenchmarkRunner`, `QualityScorer` (weighted: no_error 0.5, latency 0.3, file_size 0.2)
- **API**: `/api/models` (5 endpoints), `/api/benchmark` (7 endpoints)
- **Migrations**: `0010_media.sql`, `0011_model_registry.sql` — 6 tables + 8 indexes
- **Feature flags**: media_generation, media_image, media_video (F), media_local_storage, model_registry, model_registry_seed, benchmark_lab (F), benchmark_auto_quality (F)

### Sprint 7A — Prompt Intelligence Engine
- **Execution Profiles** (6): Research, Academic Report, Marketing, Product Advertisement, Presentation, Video Generation
- **Prompt Profiles** (10 seed): product_ad, food_photography, travel_poster, social_media, research_report, academic_report, presentation, video_ad, ui_design, logo_design
- **PromptIntelligenceEngine**: intent detection (Arabic + English, 20+ keywords), context assembly, template rendering, model selection
- **PromptMemory**: record_success, record_failure, is_blacklisted, get_avg_score, get_consecutive_failures
- **PromptProfileRepository**: full CRUD + version history
- **Migration**: `0012_prompt_intelligence.sql` — 4 tables + 6 indexes
- **API**: 9 endpoints under `/api/prompt`

### Sprint 7B — Production Integration
- **Planner**: `prompt_intelligence` intent (AUTO) added to MATRIX + KEYWORDS
- **All 4 services wired**: ResearchService, ReportService, PresentationService, MediaService route through PIE when flag enabled
- **ProviderSelector**: benchmark-aware `_quality_score()` with BenchmarkRepository fallback
- **HandlerRegistry**: single PIE instance injected into all services

### Sprint 7C — Learning Loop
- **Context Integration fixed**: `_gather_context()` now calls `ContextEngine.build()` — real workspace context + memories injected
- **Learning loop activated**: `record_success()`/`record_failure()` called from all 4 services
- **Score consumption**: `_select_model()` ranks models by `get_avg_score()` — highest-scored wins

### Sprint 8A — Operations Layer
- **Usage Center**: `usage_log` table, UsageService (record, summary, breakdowns)
- **Cost Monitoring**: CostService (total, by-provider, by-model, daily)
- **Storage Management**: StorageService (artifact counts, published assets, retention CRUD)
- **Cleanup System**: CleanupService (dry-run, execute, keep-metadata, audit log); default 4-day retention
- **Provider Dashboard**: ProviderDashboardService (status, error rate, avg latency, models)
- **API**: 17 endpoints under `/api/operations`
- **Migration**: `0013_operations_layer.sql` — 3 tables + 3 indexes
- **Feature flags**: operations_layer (T), cleanup_manual (T)

### Sprint 8B — Operations UI
- Sidebar nav item ⚙️ العمليات
- 5 tabs: Usage, Providers, Costs, Storage, Cleanup
- Consumes all 17 operations endpoints
- Mini bar chart, status badges, retention table, cleanup execute with confirmation
- Pure frontend — no backend changes

---

## 4. Current Architecture

```
User → Planner (35 intents) → PromptIntelligenceEngine.resolve()
  ├─ ContextEngine.build() → real workspace context + memories
  ├─ ExecutionProfile.match() → PromptProfile
  ├─ _select_model()
  │   ├─ is_blacklisted() filter
  │   └─ get_avg_score() ranking
  ├─ _render_template() → model-specific prompt
  └─ PromptPackage
       │
       ▼
  Service (Research / Report / Presentation / Media)
       │
       ├─ Success → record_success()
       └─ Error → record_failure()
            │
            ▼
       Adapter → Artifact
            │
            ▼
       UsageService.record()
```

**Core components** (always enabled):
- `toll/planner/` — Planner with 35 intents, 3 modes (Strict/Balanced/Fast)
- `toll/workflow/` — WorkflowEngine with handler registration, approval gating
- `toll/memory/` — MemoryGraph (5 types: global, brand, university, project, knowledge)
- `toll/context/` — ContextEngine (workspace + memory + conversation context)
- `toll/core/` — Config, Storage, Settings, FeatureFlags, ConnectionManager, ProviderRegistry, ProviderSelector
- `toll/ports/` — ABCs for LLM, Search, Research, Media, Notebook
- `api/` — 12 routers, FastAPI application

**Optional layers** (feature-flagged):
- `toll/application/` — ResearchService, ReportService, PresentationService, MediaService, CarouselService, NotebookService, OpenDesignService
- `toll/prompt/` — PromptIntelligenceEngine, PromptProfileService, PromptMemory, ExecutionProfileRepository
- `toll/model_registry/` — ModelRegistryService, ModelRepository
- `toll/benchmark/` — BenchmarkService, BenchmarkRunner, QualityScorer
- `toll/operations/` — UsageService, CostService, StorageService, CleanupService, ProviderDashboardService
- `toll/research/` — WebResearcher, SourceManager, DedupEngine, CitationEngine, ImportanceScorer, MemoryService
- `toll/engine/renderers/` — 8 renderers (carousel, report, presentation, code, preview, research preview, image_preview, video_preview)

---

## 5. Prompt Intelligence Architecture

**Enabled by**: `prompt_intelligence` flag (default: False)

**Execution Profiles** (6, in-memory):
- Research → research_report, academic_report, literature_review
- Academic Report → academic_report, citation_paper, thesis_section
- Marketing → product_ad, social_media, brand_copy, seo_content
- Product Advertisement → product_ad, food_photography, packaging_design
- Presentation → presentation, slide_deck, pitch_deck
- Video Generation → video_ad, video_presentation, short_form_video

**Prompt Profiles** (10, DB-backed, versioned):
product_ad, food_photography, travel_poster, social_media, research_report, academic_report, presentation, video_ad, ui_design, logo_design

**Engine Pipeline**:
1. `resolve(user_input, media_type, execution_profile_id, model_id)`
2. Intent detection (keyword map, Arabic + English)
3. Profile matching (execution sub-profiles → exact → tag → first)
4. Context assembly via `ContextEngine.build()`
5. Model selection via `_select_model()` (blacklist filter + avg_score ranking)
6. Template rendering via `{variable}` string replacement

**Memory integration**:
- `record_success(profile_id, model_id, prompt, artifact_id)` — called after every successful generation
- `record_failure(profile_id, model_id, reason)` — called on generation errors
- `is_blacklisted(profile_id, model_id)` — filters out failing models
- `get_avg_score(profile_id, model_id)` — ranks models by historical quality

---

## 6. Media Architecture

**Enabled by**: `media_generation` flag (default: True), `media_image` (T), `media_video` (F)

**Components**:
- `MediaPort` ABC — `generate(MediaRequest) → MediaResult`
- `ReplicateMediaAdapter` — image generation via Replicate API (requires `replicate` package + API token)
- `OllamaMediaAdapter` — stub (returns "not yet supported")
- `FsMediaStorage` — filesystem save/get/delete under `data/media/`
- `MediaService` — orchestrates provider resolution, PIE prompt optimization, storage, artifact creation
- `ModelRegistryService.find_best()` — returns first active model (no ranking)

**Current limitations**: Image generation only. Video framework-ready (ArtifactType.VIDEO, MediaRequest.duration, content_type for video/mp4) but no adapter implemented.

---

## 7. Operations Architecture

**Enabled by**: `operations_layer` flag (default: True)

**Database tables**:
- `usage_log` — per-request granular usage (provider, model, media_type, cost, duration, success/error)
- `retention_policies` — configurable cleanup policies (default: 4 days, keep metadata)
- `cleanup_log` — cleanup action audit trail

**Services**:
- `UsageService` — record(), summary(), by_provider(), by_model(), daily_cost(), recent()
- `CostService` — total(), by_provider(), by_model(), daily()
- `StorageService` — summary(), published_assets(), pending_cleanup(), retention_policies(), upsert/delete policy
- `CleanupService` — simulate() (dry-run), execute() (file deletion + metadata preservation), log()
- `ProviderDashboardService` — summary() (all providers with status/error rate/latency), provider_detail()

**API**: 17 read/write endpoints under `/api/operations`

**UI**: 5-tab Operations panel in ZUNO sidebar

---

## 8. Approved Roadmap

### Completed
- Sprint 7A: Prompt Intelligence Engine core
- Sprint 7B: Production integration into all services
- Sprint 7C: Learning loop, context fix, score consumption

### Next: Sprint 9 — Video & Audio Generation
- Video adapter (Veo, Runway, MiniMax) via MediaPort — enable `media_video`
- Audio adapter (ElevenLabs, Kokoro TTS) for NotebookLM audio overviews
- Character consistency — seed/face anchor preservation
- Estimated: 8-10 days, ~12 files, 30 tests

### Future
- Sprint 8C: Operations UI polish (cache layer, usage_aggregates, advanced analytics)
- Sprint 10: Research provider expansion (Semantic Scholar, arXiv, Crossref)
- Sprint 11: Advanced memory (RAG pipeline, hybrid search)
- Sprint 12: Production hardening (multi-user, PostgreSQL, auth)

---

## 9. Publishing Vision

- Artifacts are stored with `rendered_path` and `preview_url`
- Published assets are tracked via `StorageService.published_assets()`
- Default retention: 4 days (configurable per workspace/media type)
- Cleanup deletes rendered files but keeps metadata (artifact record + content JSON)
- Dry-run mode always default — explicit confirmation required for execution

---

## 10. Retention Strategy

- **Default policy**: 4 days, keep metadata, enabled
- **Table**: `retention_policies` (workspace_type, workspace_id, media_type, retention_days, keep_metadata, enabled)
- **CleanupService.execute()**: for each enabled policy, find artifacts older than retention_days with rendered_path set; delete the file; set rendered_path = NULL; log to cleanup_log
- **API**: simulate (dry-run) → execute (with confirmation) → log (audit trail)
- **No auto-scheduled cleanup yet** — manual trigger only via API/UI

---

## 11. Brand DNA Decisions

- **Name**: تول (TOOL) — means "to unify" in Arabic
- **Logo**: "ت" — first letter of تول, gradient (primary → accent)
- **Direction**: RTL (right-to-left) — Arabic-first interface
- **Philosophy**: Collaborative operator, not a chatbot. Discuss → Plan → Approve → Execute → Learn
- **Tone**: Professional, academic, design-conscious
- **Language**: Arabic primary, English secondary

---

## 12. Approved Themes

| Property | Dark | Light |
|----------|------|-------|
| bg | #1a1a2e | #f8fafc |
| bg2 | #16213e | #f1f5f9 |
| bg3 | #0f3460 | #e2e8f0 |
| sidebar | #111827 | #ffffff |
| sidebar-hover | #1f2937 | #f1f5f9 |
| surface | #1f2937 | #ffffff |
| primary | #38bdf8 | #0ea5e9 |
| primary-dim | #0ea5e9 | #0284c7 |
| accent | #a78bfa | #a78bfa |
| text | #f1f5f9 | #0f172a |
| text2 | #94a3b8 | #475569 |
| text3 | #64748b | #94a3b8 |
| border | #1e293b | #e2e8f0 |
| border2 | #334155 | #cbd5e1 |
| send | #3b82f6 | #3b82f6 |
| radius | 12px | 12px |
| radius-lg | 20px | 20px |

---

## 13. Approved Typography

- **Primary**: `system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif`
- **Code**: `'SF Mono', 'Fira Code', monospace`
- **Report**: `'Times New Roman', serif`
- **Base size**: 16px (body)
- **Header sizes**: 1.15rem (sidebar h1), 1.1rem (panel headers), 1.5rem (card titles)
- **Body text**: 0.85rem - 0.9rem
- **Meta/labels**: 0.75rem - 0.85rem
- **Line height**: 1.7 (body), 1.8 (lists)

---

## 14. Content Archetypes

| Archetype | Handler | Artifact Type | Renderer |
|-----------|---------|---------------|----------|
| Carousel | CarouselService | CAROUSEL | carousel_preview |
| Report | ReportService | REPORT | report_renderer |
| Presentation | PresentationService | PRESENTATION | presentation_renderer |
| Code | — | CODE | code_preview |
| Research | ResearchService | RESEARCH | research_preview |
| Image Generation | MediaService (Replicate) | IMAGE_GEN | media_renderer (image_preview) |
| Video Generation | MediaService (future) | VIDEO | media_renderer (video_preview) |
| Notebook | NotebookService | — | — |
| Open Design | OpenDesignService | — | — |

---

## 15. Future Sprint Order

1. **Sprint 9**: Video & Audio Generation (Veo, Runway, ElevenLabs) — 8-10d
2. **Sprint 8C**: Operations polish (cache layer, aggregates) — 5-7d
3. **Sprint 10**: Research provider expansion (Semantic Scholar, arXiv) — 8-12d
4. **Sprint 11**: Advanced memory (RAG pipeline, hybrid search) — 10-14d
5. **Sprint 12**: Production hardening (multi-user, PostgreSQL, auth) — 10-15d

**Do not start a sprint until the previous sprint is fully closed** (commit, tag, push, docs).
