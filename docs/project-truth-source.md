# ZUNO (تول) — Project Truth Source

> **Version**: 0.8.0-beta  
> **Tag**: v0.8b-operations-ui  
> **Commit**: 749e291  
> **Tests**: 453 passing  
> **Purpose**: Single canonical source of truth — only final approved decisions. No historical alternatives, no brainstorming, no deprecated roadmaps.

---

## 1. Current Version

| Field | Value |
|-------|-------|
| Version | 0.8.0-beta |
| Latest Tag | v0.8b-operations-ui |
| Latest Commit | 749e291 |
| Test Count | 453 passing |
| Feature Flags | 54 across 7 sprint groups |
| State | Operations Layer active — usage tracking, storage management, cleanup system, provider dashboard operational. Prompt Intelligence Engine is production-integrated into all generation flows with active learning loop and context-aware prompt generation. |

---

## 2. Completed Sprints

### Sprint 6A — Media Foundation
- `MediaService`, `ReplicateMediaAdapter`, `FsMediaStorage`, `MediaPreviewRenderer`
- `ModelRegistryService`, `ModelRepository`, 4 seed models (flux-schnell, flux-pro, sdxl, dall-e-3)
- `BenchmarkService`, `BenchmarkRunner`, `QualityScorer` (no_error 0.5, latency 0.3, file_size 0.2)
- API: `/api/models` (5 endpoints), `/api/benchmark` (7 endpoints)
- Migrations: `0010_media.sql`, `0011_model_registry.sql`
- Flags: media_generation (T), media_image (T), media_video (F), media_local_storage (T), model_registry (T), model_registry_seed (T), benchmark_lab (F), benchmark_auto_quality (F)

### Sprint 7A — Prompt Intelligence Engine
- 6 Execution Profiles: Research, Academic Report, Marketing, Product Advertisement, Presentation, Video Generation
- 10 seed Prompt Profiles: product_ad, food_photography, travel_poster, social_media, research_report, academic_report, presentation, video_ad, ui_design, logo_design
- `PromptIntelligenceEngine`: intent detection (Arabic + English, 20+ keywords), context assembly, template rendering, model selection
- `PromptMemory`: record_success, record_failure, is_blacklisted, get_avg_score, get_consecutive_failures
- `PromptProfileRepository`: full CRUD + version history
- Migration: `0012_prompt_intelligence.sql` (4 tables + 6 indexes)
- API: 9 endpoints under `/api/prompt`

### Sprint 7B — Production Integration
- Planner: `prompt_intelligence` intent (AUTO) added to MATRIX + KEYWORDS
- All 4 services wired: ResearchService, ReportService, PresentationService, MediaService route through PIE when flag enabled
- ProviderSelector: benchmark-aware `_quality_score()` with BenchmarkRepository fallback
- HandlerRegistry: single PIE instance injected into all services

### Sprint 7C — Learning Loop
- Context Integration fixed: `_gather_context()` calls `ContextEngine.build()` — real workspace context + memories injected
- Learning loop activated: `record_success()`/`record_failure()` called from all 4 services
- Score consumption: `_select_model()` ranks models by `get_avg_score()` — highest-scored wins

### Sprint 8A — Operations Layer
- Usage Center: `usage_log` table, UsageService (record, summary, breakdowns)
- Cost Monitoring: CostService (total, by-provider, by-model, daily)
- Storage Management: StorageService (artifact counts, published assets, retention CRUD)
- Cleanup System: CleanupService (dry-run, execute, keep-metadata, audit log); default 4-day retention
- Provider Dashboard: ProviderDashboardService (status, error rate, avg latency, models)
- API: 17 endpoints under `/api/operations`
- Migration: `0013_operations_layer.sql` (3 tables + 3 indexes)
- Flags: operations_layer (T), cleanup_manual (T)

### Sprint 8B — Operations UI
- Sidebar nav item ⚙️ العمليات
- 5 tabs: Usage, Providers, Costs, Storage, Cleanup
- Consumes all 17 operations endpoints
- Mini bar chart, status badges, retention table, cleanup execute with confirmation
- Pure frontend — no backend changes

---

## 3. Current Architecture

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

### Core Components (always enabled)
- `toll/planner/` — Planner with 35 intents, 3 modes (Strict/Balanced/Fast)
- `toll/workflow/` — WorkflowEngine with handler registration, approval gating
- `toll/memory/` — MemoryGraph (5 types: global, brand, university, project, knowledge)
- `toll/context/` — ContextEngine (workspace + memory + conversation context)
- `toll/core/` — Config, Storage, Settings, FeatureFlags, ConnectionManager, ProviderRegistry, ProviderSelector
- `toll/ports/` — ABCs for LLM, Search, Research, Media, Notebook
- `api/` — 12 routers, FastAPI application

### Optional Layers (feature-flagged)
- `toll/application/` — ResearchService, ReportService, PresentationService, MediaService, CarouselService, NotebookService, OpenDesignService
- `toll/prompt/` — PromptIntelligenceEngine, PromptProfileService, PromptMemory, ExecutionProfileRepository
- `toll/model_registry/` — ModelRegistryService, ModelRepository
- `toll/benchmark/` — BenchmarkService, BenchmarkRunner, QualityScorer
- `toll/operations/` — UsageService, CostService, StorageService, CleanupService, ProviderDashboardService
- `toll/research/` — WebResearcher, SourceManager, DedupEngine, CitationEngine, ImportanceScorer, MemoryService
- `toll/engine/renderers/` — 8 renderers (carousel, report, presentation, code, preview, research preview, image_preview, video_preview)

---

## 4. Approved Roadmap

### Completed
- Sprint 7A: Prompt Intelligence Engine core
- Sprint 7B: Production integration into all services
- Sprint 7C: Learning loop, context fix, score consumption
- Sprint 8A: Operations Layer backend
- Sprint 8B: Operations UI

### Sprint 9A — Brand DNA Engine
- Brand DNA system — store and apply brand identity (fonts, colors, logos, voice)
- KO Ghorab, Dast Nevis, DIN Next Arabic brand typography integration
- Brand style profiles with workspace-level application
- Estimated: 6-8 days

### Sprint 9B — HTML Design Engine
- Generate brand-compliant HTML designs (social cards, posters, banners, ads)
- Template engine using brand DNA profiles for automatic styling
- Dark/light theme generation per brand
- Export-ready HTML output
- Estimated: 6-8 days

### Sprint 10 — Publish Layer
- One-click publish from Artifact to web/storage
- Public share links with expiration
- Social media card generation
- Archive with retention policy enforcement
- Estimated: 8-10 days

### Future (no sprint assigned)
- Video & Audio Generation (Veo, Runway, ElevenLabs, Kokoro)
- Research provider expansion (Semantic Scholar, arXiv, Crossref)
- Advanced memory (RAG pipeline, hybrid search)
- Production hardening (multi-user, PostgreSQL, auth)

---

## 5. Brand DNA

### Philosophy
- **Mission**: توحيد — unify creativity, learning, research, productivity, design, development
- **Core belief**: Collaborative operator, not a chatbot
- **Workflow**: Discuss → Plan → Approve → Execute → Learn
- **Tone**: Professional, academic, design-conscious
- **Language**: Arabic-first, English-secondary
- **Direction**: RTL (right-to-left)
- **Relationship**: Collaborative partner, not a servant

### Number Chronicles
- Version: `v{major}.{sprint-letter}{sprint-number}-{descriptive-slug}`
- Feature flag: `{area}_{feature}` = True | False
- Migration: `{NNNN}_{description}.sql`
- Tags pushed to origin and protected in GitHub Releases

### Logomark
- Primary mark: "ت" — first letter of تول
- Rendering: 32×32px, border-radius 8px, gradient background `linear-gradient(135deg, var(--primary), var(--accent))`
- Text: White, 700 weight, centered
- Placement: Sidebar header, left of "تول" wordmark

---

## 6. Typography

### UI Typography (ZUNO Application)
- Primary interface: `system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif`
- Code/monospace: `'SF Mono', 'Fira Code', monospace`
- Reports (print-style): `'Times New Roman', serif`
- Base size: 16px (body)
- Headers: 1.15rem (sidebar h1), 1.1rem (panel headers), 1.5rem (card titles)
- Body: 0.85rem — 0.9rem
- Meta/labels: 0.75rem — 0.85rem
- Line heights: 1.7 (body), 1.8 (lists)
- No `@font-face` or custom font loading — system fonts only
- RTL alignment for Arabic, LTR for code/English
- Monospace for code previews, serif for report previews

### Brand Typography (Generated Assets)
| Font | Role | Usage |
|------|------|-------|
| KO Ghorab | Arabic display headline | Titles, hero text, large headings, poster headers |
| Dast Nevis | Arabic decorative / calligraphic | Signatures, artistic elements, ornamental text |
| DIN Next Arabic | Arabic UI / body | Body text, labels, descriptions, buttons in brand assets |

- KO Ghorab for display only — never below 24px
- Dast Nevis for accent only — never for readable content
- DIN Next Arabic for all Arabic body text in generated assets
- Brand fonts loaded only during asset generation — not in core ZUNO UI
- Fallback chain: KO Ghorab → DIN Next Arabic → system-ui → sans-serif

---

## 7. Themes

### Dark Theme (default)
```
--bg:           #1a1a2e    --primary:      #38bdf8    --text:  #f1f5f9
--bg2:          #16213e    --primary-dim:  #0ea5e9    --text2: #94a3b8
--bg3:          #0f3460    --accent:       #a78bfa    --text3: #64748b
--sidebar:      #111827    --accent2:      #f472b6    --border:#1e293b
--sidebar-hover:#1f2937    --send:         #3b82f6    --border2:#334155
--surface:      #1f2937    --send-hover:   #2563eb
--surface-hover:#374151    --radius:       12px       --radius-lg: 20px
```

### Light Theme (toggle)
```
--bg:           #f8fafc    --primary:      #0ea5e9    --text:  #0f172a
--bg2:          #f1f5f9    --primary-dim:  #0284c7    --text2: #475569
--bg3:          #e2e8f0    --accent:       #a78bfa    --text3: #94a3b8
--sidebar:      #ffffff    --border:       #e2e8f0
--sidebar-hover:#f1f5f9    --border2:      #cbd5e1
--surface:      #ffffff    --send:         #3b82f6
```

### Status Badge Colors (shared)
- ok: rgba(34,197,94,.15) bg, #22c55e text
- warn: rgba(250,204,21,.15) bg, #eab308 text
- err: rgba(239,68,68,.15) bg, #ef4444 text

### Application
- Theme toggles via `classList.toggle('light')` on `:root`
- All components use CSS variables — no hardcoded colors
- Transition: `background .3s, color .3s`

---

## 8. Publishing Vision

- Artifacts stored with `rendered_path` and `preview_url`
- Published assets tracked via `StorageService.published_assets()`
- Default retention: 4 days (configurable per workspace/media type)
- Cleanup deletes rendered files but keeps metadata (artifact record + content JSON)
- Dry-run mode always default — explicit confirmation required for execution
- Sprint 10 will add one-click publish, public share links with expiration, social card generation

---

## 9. Retention Strategy

- **Default policy**: 4 days, keep metadata, enabled
- **Table**: `retention_policies` (workspace_type, workspace_id, media_type, retention_days, keep_metadata, enabled)
- **CleanupService.execute()**: for each enabled policy, find artifacts older than retention_days with rendered_path set; delete the file; set rendered_path = NULL; log to cleanup_log
- **API flow**: simulate (dry-run) → execute (with confirmation) → log (audit trail)
- **No auto-scheduled cleanup yet** — manual trigger only via API/UI
