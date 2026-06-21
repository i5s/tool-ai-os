# Sprint 7B — Prompt Intelligence Integration — Completion Report

> **Status**: Complete  
> **Tag**: `v0.7b-prompt-intelligence-integration`  
> **Commit**: `a85dcf7`  
> **Before**: Sprint 7A (v0.7a-prompt-intelligence-core)

---

## What Sprint 7B Solved

The Sprint 7A audit identified that Prompt Intelligence Engine was an **isolated subsystem** — reachable only via its dedicated API endpoint, with no connections to production workflows. Sprint 7B completed 6 integration points across 7 files:

---

## 1. Planner Integration

| Before | After |
|--------|-------|
| `prompt_intelligence` not in `MATRIX` or `KEYWORDS` | `prompt_intelligence: ApprovalLevel.AUTO` in MATRIX; 4 keywords in KEYWORDS |
| Handler `prompt_intelligence` registered but never fired | Handler now reachable via Planner's intent resolution |

**File**: `toll/planner/planner.py`
- Added `"prompt_intelligence": ApprovalLevel.AUTO` to MATRIX
- Added keywords: "optimize prompt", "enhance prompt", "prompt intelligence", "prompt enhance", "تحسين البرومبت"

## 2. ProviderSelector — Benchmark-Aware Ranking

| Before | After |
|--------|-------|
| `_quality_score()` hardcoded to `{"opencode": 0.9, "ollama": 0.5}` | Injects `BenchmarkRepository`, queries `avg_scores()` when `benchmark_auto_quality` flag is enabled |
| No benchmark data consumption | Falls back to static scores when no benchmark data exists |

**File**: `toll/core/provider_selector.py`
- Added `benchmark_repo` constructor parameter
- In `_quality_score()`: if `benchmark_auto_quality` is enabled and benchmark data exists, use `avg_quality_auto`; else fall back to static scores

## 3. PromptMemory — Blacklist Activation

| Before | After |
|--------|-------|
| `engine.py:150` called `is_blacklisted()` but discarded result with `pass` | Blacklist check moved to `_select_model()` — filters out blacklisted models from model registry results |
| 4 of 5 `PromptMemory` methods were dead code | `is_blacklisted()` now has production effect; remaining methods ready for Sprint 7C recording hooks |

**File**: `toll/prompt/engine.py`
- Removed dead `pass` no-op
- Added blacklist filtering in `_select_model()` — queries `list(media_type, status="active")` then filters by `is_blacklisted()` before returning the first non-blacklisted model

## 4. ResearchService — PIE Integration

| Before | After |
|--------|-------|
| No `prompt_intelligence` parameter | Accepts optional `PromptIntelligenceEngine` |
| `_synthesize()` used default AI provider | PIE resolves model_id with `execution_profile_id="research"`; synthesized with explicit provider_name |

**File**: `toll/application/research_service.py`
- Added `prompt_intelligence: Any = None` constructor parameter
- In `execute()`: if PIE enabled, call `PIE.resolve(topic, "text", "research")` to get model_id
- Modified `_synthesize()` to accept optional `model_id` parameter — passes as `provider_name` to `AI.ask()`

## 5. ReportService — PIE Integration

| Before | After |
|--------|-------|
| No `prompt_intelligence` or `flags` parameters | Accepts both |
| `ProviderSelector.select()` used exclusively | PIE resolves model_id with `execution_profile_id="academic_report"` when enabled |

**File**: `toll/application/report_service.py`
- Added `flags`, `prompt_intelligence` constructor parameters
- In `execute()`: if PIE enabled, resolve model_id; use PIE result as override for `provider_name`

## 6. PresentationService — PIE Integration

| Before | After |
|--------|-------|
| No `prompt_intelligence` or `flags` parameters | Accepts both |
| Same pattern as ReportService | Same pattern |

**File**: `toll/application/presentation_service.py`
- Same changes as ReportService

## 7. MediaService — PIE Integration

| Before | After |
|--------|-------|
| No `prompt_intelligence` parameter | Accepts optional `PromptIntelligenceEngine` |
| Raw prompt passed directly to adapter | If PIE enabled, prompt is optimized through `PIE.resolve()` before generation |

**File**: `toll/application/media_service.py`
- Added `prompt_intelligence: Any = None` constructor parameter
- In `generate()`: if PIE enabled, call `PIE.resolve(prompt, media_type)` and use `pkg.prompt` as the actual prompt

## 8. HandlerRegistry — Central Wiring

**File**: `toll/application/handler_registry.py`
- Creates `BenchmarkRepository` instance (if `benchmark_lab` enabled) and injects into `ProviderSelector`
- Creates single `PromptIntelligenceEngine` instance (if `prompt_intelligence` enabled)
- Injects PIE into all 4 services: `ReportService`, `PresentationService`, `ResearchService`, `MediaService`
- Passes `FeatureFlags` to `ReportService` and `PresentationService` (previously missing)

---

## Request Lifecycle Diagram (After Sprint 7B)

```
User Input
    │
    ▼
Planner (toll/planner/planner.py)
    ├─ Detects intent (including "prompt_intelligence")
    ├─ Sets approval level
    └─ Returns Plan
         │
         ▼
WorkflowEngine (toll/workflow/engine.py)
    ├─ Dispatches to handler by intent
    └─ Calls handler.execute(plan)
         │
         ▼
    ┌──── Handler ──────────────────────────────────────────┐
    │                                                        │
    │  ResearchService.execute()                             │
    │    ├─ PIE.resolve(topic, "text", "research") ──► model │
    │    └─ _synthesize(topic, model_id=model)               │
    │                                                        │
    │  ReportService.execute()                               │
    │    ├─ PIE.resolve(title, "text", "academic_report")    │
    │    └─ AI.ask(prompt, provider_name=model_id)           │
    │                                                        │
    │  PresentationService.execute()                         │
    │    ├─ PIE.resolve(title, "text", "presentation")       │
    │    └─ AI.ask(prompt, provider_name=model_id)           │
    │                                                        │
    │  MediaService.generate()                               │
    │    ├─ PIE.resolve(prompt, media_type) ► optimized      │
    │    └─ adapter.generate(optimized_prompt)               │
    │                                                        │
    └────────────────────────────────────────────────────────┘
         │
         ▼
    ProviderSelector (benchmark-aware)
         │
         ▼
    Adapter → Artifact
```

---

## Test Results

- **Total**: 422 passed, 2 skipped (was 407)
- **New**: 15 tests
  - ProviderSelector benchmark-aware: 4 tests (benchmark data, fallback, flag gate, unknown provider)
  - Engine blacklist: 2 tests (skip blacklisted, allow non-blacklisted)
  - Service PIE wiring: 5 tests (Report/Presentation/Research/Media accept PIE, Media optimizes prompt)
  - Planner intent: 4 tests (MATRIX check, English keyword, Arabic keyword, AUTO level)
- **No regressions**

## Files Changed

| File | Change Type | Lines Changed |
|------|-------------|---------------|
| `toll/planner/planner.py` | Modified | +6 |
| `toll/core/provider_selector.py` | Modified | +17 |
| `toll/prompt/engine.py` | Modified | +9, -3 |
| `toll/application/research_service.py` | Modified | +16, -1 |
| `toll/application/report_service.py` | Modified | +19, -3 |
| `toll/application/presentation_service.py` | Modified | +20, -3 |
| `toll/application/media_service.py` | Modified | +16 |
| `toll/application/handler_registry.py` | Modified | +25, -26 |
| `docs/sprint-7a-integration-audit.md` | New | — |
| `tests/application/test_pie_integration.py` | New | 5 tests |
| `tests/core/test_provider_selector_benchmark.py` | New | 4 tests |
| `tests/planner/test_prompt_intelligence_intent.py` | New | 4 tests |
| `tests/prompt/test_engine_blacklist.py` | New | 2 tests |

## Gap Closure (from Sprint 7A Audit)

| Gap | Status |
|-----|--------|
| Planner never emits `prompt_intelligence` intent | ✅ Closed |
| ResearchService bypasses PIE | ✅ Closed |
| ReportService bypasses PIE | ✅ Closed |
| PresentationService bypasses PIE | ✅ Closed |
| MediaService bypasses PIE | ✅ Closed |
| Blacklist check is a no-op (`pass`) | ✅ Closed |
| `ProviderSelector._quality_score()` is hardcoded stub | ✅ Closed |
| 4 of 5 PromptMemory methods are dead code | ⚠️ Partially — `record_success`/`record_failure` hooks in services deferred to Sprint 7C |
| No benchmark data flows to provider selection | ✅ Closed (opt-in via `benchmark_auto_quality` flag) |
