# Post-Sprint 7B Architecture Audit — ZUNO (تول)

> **Date**: 2026-06-22  
> **Methodology**: Source-of-truth doc verification (VISION.md, ARCHITECTURE.md, PROJECT_STATE.md, TODO.md, KNOWN_GAPS.md) against actual source code inspection  
> **Scope**: All 10 architectural layers

---

## Source-of-Truth Verification

| Doc Claim | Verified? | Notes |
|-----------|-----------|-------|
| MemoryGraph has 5 memory types | ✅ | `toll/memory/graph.py` line 8 — global, brand, university, project, knowledge |
| ResearchMemory uses MemoryGraph | ✅ | `toll/research/memory_service.py` line 49 — wraps MemoryGraph |
| PromptMemory has 5 methods | ✅ | `toll/prompt/memory.py` lines 14-64 — all implemented |
| Blacklist consumed in `_select_model()` | ✅ | `toll/prompt/engine.py` line 154 — active filter (Sprint 7B fix) |
| `_gather_context()` calls ContextEngine | ❌ | Calls nonexistent `get_active_context()` method — silently fails via `except Exception` |
| ProviderSelector uses benchmark data | ✅ | `toll/core/provider_selector.py` lines 63-66 — when flag enabled |
| Planner has 25 intents | ❌ | **35 intents** (15 AUTO, 7 PLAN_ONLY, 13 APPROVAL) — doc is outdated |
| ResearchService routes through PIE | ✅ | `toll/application/research_service.py` lines 53-57 |
| MediaService optimizes prompt through PIE | ✅ | `toll/application/media_service.py` lines 50-56 |
| Replicate supports only image | ✅ | `toll/adapters/media/replicate.py` line 31 — `["image"]` only |
| 4 seed models in ModelRegistry | ✅ | `toll/model_registry/seed.py` — flux-schnell, flux-pro, sdxl, dall-e-3 |
| `find_best()` just returns first | ✅ | `toll/model_registry/service.py` line 74 — no ranking |
| `benchmark_auto_quality` defaults to False | ✅ | `toll/core/feature_flags.py` line 80 — but VISION.md says True |
| Only DuckDuckGo research provider implemented | ✅ | `toll/application/research_service.py` lines 162-166 |
| No video adapter exists | ✅ | `toll/adapters/media/` has no video files |
| Usage tracking is basic daily counts | ✅ | `toll/core/limiter.py` — single `INSERT INTO usage` |

---

## Layer-by-Layer Audit

### 1. Memory Layer
**Files**: `toll/memory/graph.py`, `toll/research/memory_service.py`, `toll/prompt/memory.py`

Three separate memory systems with **zero cross-communication**:
- **MemoryGraph** — stores to `memories` table, used by WorkspaceManager and ContextEngine
- **PromptMemory** — stores to `prompt_scores`/`prompt_blacklist` tables, completely standalone
- **ResearchMemoryService** — wraps MemoryGraph, adds its own `research_memory_meta` table

No system can correlate a prompt profile score with a user memory. Prompt quality data is invisible to the main memory system.

### 2. Context Layer
**Files**: `toll/prompt/engine.py`, `toll/context/engine.py`

**Broken integration**: PIE's `_gather_context()` at line 183 calls `self.context_engine.get_active_context()`, but `ContextEngine` has no such method (only `build()`). The `except Exception` at line 188 silently swallows the `AttributeError`. The prompt receives only hardcoded defaults — no workspace context, no memory, no conversation history.

### 3. Prompt Intelligence Layer
**Files**: `toll/prompt/engine.py`, `toll/prompt/memory.py`

| Component | Status |
|-----------|--------|
| Intent detection | ✅ Working (20+ keywords, Arabic + English) |
| Profile matching | ✅ Working (execution → sub-profile → exact → tag → first) |
| Template rendering | ✅ Working (string replace) |
| Model selection via blacklist | ✅ Working (Sprint 7B fix) |
| Model selection via avg_score | ❌ `get_avg_score()` never called — no quality ranking |
| Context injection | ❌ Broken — calls nonexistent method |
| record_success / record_failure wiring | ❌ **Never called** from any service — learning loop is dead |

### 4. Model Layer
**Files**: `toll/model_registry/service.py`, `toll/core/provider_selector.py`

- `ModelRegistryService.find_best()` returns `models[0]` — no ranking whatsoever
- `ProviderSelector._quality_score()` has a benchmark-aware path, but:
  - `benchmark_auto_quality` defaults to **False**
  - `benchmark_lab` also defaults to **False** — no benchmark runs exist in production
  - The benchmark-aware path is dead code in production

### 5. Research Layer
**Files**: `toll/application/research_service.py`

- **1 of 6 planned research providers implemented**: only DuckDuckGo (via WebResearcher)
- Five provider flags (`provider_semantic_scholar`, `provider_google_scholar`, `provider_arxiv`, `provider_crossref`, `provider_zotero`) all default to False with **zero adapter files**
- Research `deep` mode is identical to standard mode (`execute_deep()` literally calls `self.execute(plan, metadata)`)

### 6. Media Layer
**Files**: `toll/ports/media.py`, `toll/adapters/media/replicate.py`, `toll/adapters/media/ollama.py`

- Image generation via Replicate: ✅ working
- Video: ❌ framework-ready (MediaRequest.duration, ArtifactType.VIDEO, content_type for video/mp4) but no adapter
- Ollama adapter: stub returning "not yet supported"
- Storage: ✅ FsMediaStorage fully functional with `data/media/` root

### 7. Workflow Layer
**Files**: `toll/planner/planner.py`, `toll/application/handler_registry.py`

- 35 intents in Planner MATRIX (doc says 25 — discrepancy)
- 16 handlers registered across 8 conditional blocks
- `prompt_intelligence` intent: ✅ AUTO level, reachable via Planner keywords

### 8. Operations Layer
**Files**: `toll/core/limiter.py`

- **Usage tracking**: bare minimum — daily counts, no per-profile/per-model granularity
- **Cost monitoring**: ❌ non-existent (cost_per_unit fields exist in Model dataclass but never accumulated)
- **Provider dashboard**: ❌ no UI
- **Caching**: ❌ no prompt-to-artifact cache
- Glob search for `*usage*`, `*cost*`, `*cache*`, `*dashboard*` in toll/ — **zero results**

### 9. Future Readiness

- **Multi-user**: ❌ `users_enabled` flag exists but no auth, no login, no tenant isolation; `WorkspaceManager` hardcodes `user_id="default"`
- **Automation**: ❌ no scheduler, no auto-retry, no event-driven workflows
- **Scalability**: ❌ SQLite only, no PostgreSQL migration path

### 10. Technical Debt

| Category | Count | Examples |
|----------|-------|---------|
| `except: pass` | 2 | `toll/core/ai.py:52`, `toll/context/engine.py:74` — silently swallows errors |
| `except Exception:` with log only | 5+ | `research_service.py:128-129`, `memory_service.py:90,97` |
| Stub adapters | 3 | OllamaMediaAdapter, NotebookLMProvider, BrowserAI |
| Doc discrepancy | 2 | Planner intent count (25→35), benchmark_auto_quality default (doc says True, code says False) |
| `# TODO` comments | 1 | `api/routers/workspaces.py` |
| `# FIXME` / `# HACK` / `# XXX` | 0 | Issues silently hidden rather than tracked |
| `NotImplementedError` | 0 | Stubs use generic error messages |

---

## Top 10 Remaining Architectural Gaps

| Rank | Gap | Severity | Effort | Sprint | Layer |
|------|-----|----------|--------|--------|-------|
| 1 | **ContextEngine integration broken** — `_gather_context()` calls nonexistent method; PIE operates blind | 🔴 HIGH | 0.5d | 7C | Context |
| 2 | **Learning loop not wired** — `record_success()`/`record_failure()` never called from any service | 🔴 HIGH | 2d | 7C | PIE |
| 3 | **Memory triply siloed** — MemoryGraph, PromptMemory, ResearchMemory have zero cross-communication | 🔴 HIGH | 4d | 8 | Memory |
| 4 | **`_select_model()` ignores historical quality** — `get_avg_score()` never called; selection effectively random | 🔴 HIGH | 1d | 7C | PIE |
| 5 | **Only 1 of 6 research providers implemented** — 5 adapter files missing | 🟡 MEDIUM | 8-12d | 10 | Research |
| 6 | **No operations layer** — no usage, cost, caching, or dashboard | 🟡 MEDIUM | 10d | 8 | Ops |
| 7 | **Benchmark integration is opt-in and never enabled** — both `benchmark_auto_quality` and `benchmark_lab` default to False | 🟡 MEDIUM | 2d | 8 | Model |
| 8 | **Video generation is framework-only** — no adapter; `media_video` flag cannot be enabled | 🟡 MEDIUM | 5-8d | 9 | Media |
| 9 | **No multi-user support** — `users_enabled` is a placeholder flag | 🟢 LOW | 10-15d | 11 | Infra |
| 10 | **Technical debt** — silent failure swallowing, stub adapters, doc discrepancies | 🟢 LOW | 3d | 8 | All |

---

## Recommended Roadmap to v1.0

### Sprint 7C — Fix Broken Integration + Close the Learning Loop (4-6d)
**Why first**: Gaps #1, #2, #4 are pure integration work — no new infrastructure needed. Without these fixes, PIE operates blind with zero feedback.

1. Fix `_gather_context()` to call `ContextEngine.build()` and extract context from the `ContextResult` (0.5d)
2. Wire `record_success()` into all 4 service flows post-generation (1d)
3. Wire `record_failure()` into all error paths (0.5d)
4. Integrate `get_avg_score()` as quality weight in `_select_model()` (1d)
5. Implicit feedback scoring from user actions (keep = positive within 60s) (1d)

### Sprint 8 — Operations Layer + Memory Unification (12-15d)
**Why second**: Without cost awareness or caching, the system is a black box. Sprint 7C makes it smart; Sprint 8 makes it observable and efficient.

1. Usage Center — per-provider, per-profile, per-generation tracking + quotas (3d)
2. Cost Monitoring — accumulate `cost_per_unit` × actual usage per session (2d)
3. Caching Layer — hash-based prompt-to-artifact cache, dedup identical requests (2d)
4. Unify PromptMemory into MemoryGraph — or create a memory registry adapter (3d)
5. Provider Dashboard — UI for benchmark results, cost breakdown, quality scores (3d)
6. Enable `benchmark_auto_quality` with automated light benchmarks on startup (1d)
7. Fix `except:` bare passes; replace stubs with `NotImplementedError` (1d)

### Sprint 9 — Media Expansion (Video + Audio) + Character Consistency (8-10d)
**Why third**: Media framework is ready but empty. Video is the most requested gap.

1. Replicate video adapter (supports runway-gen3 etc.) (3d)
2. Audio adapter for ElevenLabs / Kokoro TTS (2d)
3. Character/style consistency via seed preservation (2d)

### Sprint 10 — Research Provider Expansion (8-12d)
**Why fourth**: Five provider flags sit unused. Academic source access dramatically increases research quality.

1. Semantic Scholar adapter (2d)
2. arXiv adapter (1d)
3. Crossref adapter (1d)
4. RAG pipeline for hybrid search across all memory types (3d)

### Sprint 11 — Production Hardening (10-15d)
**Why last**: Multi-user and auth add complexity with minimal benefit to the single-user desktop experience.

1. Auth system — API keys, JWT, login (5d)
2. Tenant isolation — scoped workspaces per user (3d)
3. PostgreSQL migration path (3-4d)
4. End-to-end integration tests (3d)

---

## What Should Be Built Next and Why

**Sprint 7C — immediately.** Three HIGH-severity gaps (1, 2, 4) are pure integration work requiring zero new infrastructure:

1. **Broken ContextEngine call (0.5d)**: The single biggest defect. PIE generates prompts without any workspace context, memory, or conversation history. This fix alone restores the intended architecture — every prompt will know the active brand, project, and recent user context.

2. **Learning loop unwired (2d)**: The full PromptMemory infrastructure is built — tables, methods, queries — but **zero service flows call it**. Two days of wiring unlocks the entire self-improvement loop.

3. **Model selection ignores quality data (1d)**: `get_avg_score()` exists, has data, is never queried. Adding it as a ranking weight converts model selection from random to quality-driven.

These are **low-risk, high-impact** changes — connecting existing pieces that were built but never integrated. Total estimate: **3.5 days** for all three.
