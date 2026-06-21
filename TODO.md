# TOOL Implementation Backlog

## Sprint 0: Foundation — COMPLETE

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T1 | Feature flag framework | Done | `toll/core/feature_flags.py` |
| T2 | Fix pyproject.toml dependencies | Done | Added playwright, pinned versions, dev deps |
| T3 | Add pytest and test structure | Done | `tests/` with fixtures |
| T4 | Remove sys.path hacks | Done | Package installed editable |
| T28 | Restrict CORS | Done | Local origins only, env override |

## Sprint 1: Core Infrastructure — COMPLETE

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T5 | Add database migration system | Done | `toll/model/migrations/` |
| T6 | Define ports and adapters | Done | `toll/ports/`, `toll/adapters/` |
| T10 | Refactor Provider Layer | Done | `ProviderRegistry` in `toll/core/registry.py` |
| T11 | Fix or replace BrowserAI | Done | Replaced with DuckDuckGo search adapter |
| T12 | Wire Settings System | Done | `toll/core/settings.py` |

## Sprint 2: Memory Graph + Workspace Manager — COMPLETE

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T9 | Memory Graph v1 | Done | `toll/memory/graph.py` |
| T33 | Workspace Manager | Done | `toll/workspace/manager.py` |
| T34 | Workspace API endpoints | Done | `api/routers/workspaces.py` |
| T35 | Workspace UI + chat commands | Done | Sidebar selector + /brand, /university, /project, /semester |
| — | Conversations system | Done | `toll/core/conversations.py` |
| — | Conversation API endpoints | Done | `api/routers/conversations.py` |
| — | Update /api/chat | Done | Persists messages via ConversationStore |

## Sprint 3: Context Engine + Planner + Workflow Engine — COMPLETE

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T36 | Context Engine | Done | `toll/context/engine.py` |
| T7 | Planner v1 | Done | `toll/planner/planner.py` |
| T8 | Workflow Engine | Done | `toll/workflow/engine.py` |
| T37 | Plan/approval API | Done | `api/routers/planner.py` |
| — | Update /api/chat | Done | Uses Context Engine; Planner gates auto/plan/approval paths |

## Sprint 4: Application Services — COMPLETE

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T13 | Create toll/application/ services | Done | CarouselService, ReportService, PresentationService, etc. |
| T14 | Refactor API router | Done | 11 routers in api/routers/ |
| T15 | Refactor CLI | Done | CLI entry point |

## Sprint 5: Artifact System — COMPLETE

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T17 | AI-populated reports | Done | ReportService with AI synthesis |
| T18 | AI-populated presentations | Done | PresentationService with AI synthesis |
| T19 | AI-populated carousels | Done | CarouselService with AI synthesis |
| T20 | Artifact System | Done | `toll/model/artifact.py`, ArtifactRepository |
| T21 | Link artifacts to Memory Graph | Done | MemoryGraph stores artifact references |

## Sprint 6: Media Foundation — COMPLETE

| ID | Task | Status | Notes |
|----|------|--------|-------|
| T22 | Media Layer ports + adapters | Done | MediaPort, ReplicateMediaAdapter, FsMediaStorage |
| T23 | Model Registry | Done | ModelRegistryService, ModelRepository, seed data |
| T25 | Benchmark Lab | Done | BenchmarkService, BenchmarkRunner, QualityScorer |
| T26 | Media API endpoints | Done | /api/models (5), /api/benchmark (7) |
| T27 | Migrations 0010-0011 | Done | media_meta, media_resources, models, model_tags, benchmark_suites, benchmark_runs |

## Sprint 7A: Prompt Intelligence Engine — COMPLETE

| ID | Task | Status | Notes |
|----|------|--------|-------|
| P1 | PromptIntelligenceEngine | Done | `toll/prompt/engine.py` - intent detection, template rendering, model selection |
| P2 | Prompt Profiles (10 seed) | Done | `toll/prompt/profiles.py` - product_ad, food_photography, etc. |
| P3 | Execution Profiles (6) | Done | `toll/prompt/execution_profile.py` - Research, Marketing, etc. |
| P4 | PromptProfileRepository | Done | `toll/prompt/repository.py` - CRUD + version history |
| P5 | PromptProfileService | Done | `toll/prompt/profile_service.py` |
| P6 | PromptMemory | Done | `toll/prompt/memory.py` - success/failure/blacklist/scoring |
| P7 | Migration 0012 | Done | 4 tables + 6 indexes |
| P8 | API endpoints (9) | Done | `/api/prompt/profiles`, `/api/prompt/execution-profiles`, `/api/prompt/resolve` |
| P9 | Feature flags | Done | prompt_intelligence (F), prompt_intelligence_seed (T) |

## Sprint 7B: Prompt Intelligence Integration — COMPLETE

| ID | Task | Status | Notes |
|----|------|--------|-------|
| I1 | Planner -> PIE | Done | Added prompt_intelligence intent to MATRIX + KEYWORDS |
| I2 | Research -> PIE | Done | ResearchService.execute() routes through PIE when enabled |
| I3 | Report -> PIE | Done | ReportService.execute() routes through PIE when enabled |
| I4 | Presentation -> PIE | Done | PresentationService.execute() routes through PIE when enabled |
| I5 | Media -> PIE | Done | MediaService.generate() optimizes prompt through PIE |
| I6 | Blacklist activation | Done | engine._select_model() filters blacklisted models |
| I7 | Benchmark-aware ProviderSelector | Done | `_quality_score()` queries BenchmarkRepository when flag enabled |
| I8 | HandlerRegistry wiring | Done | Single PIE + BenchmarkRepository injected into all services |

## Sprint 7C — Prompt Learning Loop

| ID | Task | Priority | Notes |
|----|------|----------|-------|
| L1 | Wire record_success() into service flows | High | Call after each successful generation |
| L2 | Wire record_failure() into service flows | High | Call on generation errors |
| L3 | Feedback scoring from user actions | Medium | Implicit (keep within 60s = positive) + explicit (ratings) |
| L4 | Profile template tuning based on scores | Low | Flag profiles with avg_score < 0.6 for review |
| L5 | PromptMemory score integration in engine | Medium | Use get_avg_score() as weight in _select_model() |

## Sprint 8 — Operations Layer

| ID | Task | Priority | Notes |
|----|------|----------|-------|
| O1 | Usage Center | High | Per-provider request tracking, quotas, history |
| O2 | Provider Dashboard | High | Visual provider performance, benchmark results |
| O3 | Cost Monitoring | Medium | Per-provider, per-profile spend analytics |
| O4 | Caching Layer | Medium | Prompt-to-artifact cache, deduplicate identical requests |
| O5 | Provider cost comparison | Low | Side-by-side cost + quality analysis in UI |

## Sprint 9+ — Advanced

| ID | Task | Priority | Notes |
|----|------|----------|-------|
| A1 | Video generation | High | Veo, Runway, Kling adapters (enable media_video flag) |
| A2 | Audio generation | Medium | ElevenLabs, Kokoro TTS |
| A3 | Automation layer | Medium | Scheduled tasks, event-driven workflows, auto-retry |
| A4 | Multi-user support | Low | Auth, isolated workspaces, shared resources |
