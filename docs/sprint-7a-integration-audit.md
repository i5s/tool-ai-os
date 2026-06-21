# Sprint 7A — Prompt Intelligence Integration Audit

> **Date**: 2026-06-22  
> **Audit Scope**: Verify Sprint 7A is connected to the platform, not an isolated subsystem  
> **Methodology**: Source file inspection, cross-reference search, call graph tracing

---

## 1. Connected Components

### ✅ API Router — `api/routers/prompt.py`
Instantiates `PromptIntelligenceEngine` at line 137 and calls `engine.resolve()` at line 141. Endpoint `POST /api/prompt/resolve` is the **only production path** that reaches the engine today. Guarded by `flags.is_enabled("prompt_intelligence", default=False)`.

### ✅ Execution Profiles — `api/routers/prompt.py` lines 115-124
`GET /prompt/execution-profiles` and `GET /prompt/execution-profiles/{id}` call `ExecutionProfileService`, which instantiates `ExecutionProfileRepository`. Reachable via API but **not consumed by any workflow handler**.

---

## 2. Disconnected Components

### ❌ Research Service — `toll/application/research_service.py`
**Does NOT import or reference `PromptIntelligenceEngine`.** Uses `AI`, `ProviderSelector`, `SourceManager`, `CitationEngine`, `NotebookService` directly. Prompts are constructed inline in `_synthesize()` (line 191) and `_render_research()` (line 222).

**Connection point needed:** In `execute()`, before `_synthesize()`, call `PIE.resolve(topic, media_type="text", execution_profile_id="research")` to obtain model ID and prompt structure.

### ❌ Report Service — `toll/application/report_service.py`
**Does NOT import or reference `PromptIntelligenceEngine`.** Uses `AI`, `ProviderSelector`, `ReportRenderer` directly. Prompt built in `_build_prompt()` (line 70), sent via `self.ai.ask(prompt, provider_name=...)`.

**Connection point needed:** In `execute()` at line 34, replace `_build_prompt()` + `ProviderSelector.select()` with `PIE.resolve(title, media_type="text", execution_profile_id="academic_report")`.

### ❌ Presentation Service — `toll/application/presentation_service.py`
**Does NOT import or reference `PromptIntelligenceEngine`.** Identical pattern to Report Service: `_build_prompt()` at line 70, `ProviderSelector.select()` for model.

**Connection point needed:** In `execute()` at line 34, replace with `PIE.resolve(title, media_type="text", execution_profile_id="presentation")`.

### ❌ Media Service — `toll/application/media_service.py`
**Does NOT import or reference `PromptIntelligenceEngine`.** Uses `ProviderRegistry`, `ProviderSelector`, `ModelRegistryService` directly. Takes raw `params["prompt"]` with no optimization.

**Connection point needed:** In `generate()` at line 43, pass raw prompt through `PIE.resolve(prompt, media_type=media_type)` to obtain optimized prompt and resolved model ID.

---

## 3. Dead Code Risk

### 🔴 HIGH: Workflow Handler — `toll/application/handler_registry.py` lines 95-108

The `prompt_intelligence` handler is **registered but will never fire**. The Planner (`toll/planner/planner.py`) defines 40+ intents in its `MATRIX` and `KEYWORDS` dictionaries, but `prompt_intelligence` is **not among them**. No keyword trigger, no approval level, no classification path produces `Plan(intent="prompt_intelligence")`. The handler exists on paper only.

### 🔴 HIGH: PromptMemory — `toll/prompt/memory.py`

| Method | Called in Production? | Verdict |
|---|---|---|
| `record_success()` | No — only in unit tests | **DEAD CODE** |
| `record_failure()` | No — only in unit tests | **DEAD CODE** |
| `is_blacklisted()` | Called at `engine.py:150` but result **discarded** (`pass` no-op) | **INEFFECTIVE** |
| `get_avg_score()` | No — only in unit tests | **DEAD CODE** |
| `get_consecutive_failures()` | No — only in unit tests | **DEAD CODE** |

The blacklist call at `engine.py:150`:
```python
if self.prompt_memory.is_blacklisted(prompt_profile.id, preferred or ""):
    pass  # return value thrown away — zero effect on model selection
```

### 🟡 MEDIUM: ExecutionProfileService — `toll/prompt/profile_service.py`
`ExecutionProfileService.list()` and `.get()` are API-reachable but **no workflow handler ever requests an execution profile**.

---

## 4. Benchmark Readiness

### ❌ `ProviderSelector._quality_score()` — `toll/core/provider_selector.py` lines 58-63

```python
def _quality_score(self, provider: str) -> float:
    scores = {"opencode": 0.9, "ollama": 0.5}
    return scores.get(provider, 0.3)
```

**Hardcoded static stub.** Does not:
- Import or reference `BenchmarkRepository`
- Query `benchmark_runs.quality_score_auto` or `avg_scores()`
- Use the `benchmark_auto_quality` feature flag

`BenchmarkRepository.avg_scores(model_id)` (functioning, tested) returns `avg_quality_auto`, `avg_latency_ms`, `avg_cost_cents` — but **no consumer reads this data**. The benchmark system is siloed with its own API router and service.

---

## 5. Summary

| Component | File | PIE Integrated? | Production-Reachable? |
|---|---|---|---|
| Research Flow | `research_service.py` | ❌ | ❌ |
| Report Flow | `report_service.py` | ❌ | ❌ |
| Presentation Flow | `presentation_service.py` | ❌ | ❌ |
| Media Flow | `media_service.py` | ❌ | ❌ |
| Workflow Handler | `handler_registry.py` | ✅ (registered) | ❌ (no Planner intent) |
| API Router | `api/routers/prompt.py` | ✅ | ✅ |
| Execution Profiles | `execution_profile.py` | ✅ | ✅ (API only) |
| Prompt Memory | `memory.py` | Partial | ❌ (4/5 methods dead) |
| Benchmark → Selector | `provider_selector.py` | ❌ | ❌ |

---

## 6. Minimal Sprint 7B Implementation Plan

### Priority P0 — Unblock the Workflow Path (1 day)
1. **Add `prompt_intelligence` to the Planner** (`toll/planner/planner.py`):
   - Add `"prompt_intelligence": ApprovalLevel.AUTO` to `MATRIX`
   - Add `"prompt_intelligence": ["optimize prompt", "enhance prompt", "prompt intelligence"]` to `KEYWORDS`
   - Single smallest change that makes the handler live.

### Priority P1 — Wire PIE into Service Flows (2-3 days)
2. **Research Service** — Call `PIE.resolve(topic, "text", "research")` in `execute()`, feed model ID + prompt to `_synthesize()`.
3. **Report Service** — Replace `_build_prompt()` + `ProviderSelector.select()` with `PIE.resolve(title, "text", "academic_report")`.
4. **Presentation Service** — Same pattern, `execution_profile_id="presentation"`.
5. **Media Service** — Pass raw prompt through `PIE.resolve(prompt, media_type)` before generation.

### Priority P2 — Activate Prompt Memory (1 day)
6. Call `prompt_memory.record_success()` after each successful execution.
7. Call `prompt_memory.record_failure()` on error.
8. Fix `engine.py:150` — use blacklist result to skip blacklisted models.

### Priority P3 — Close the Benchmark Loop (2 days)
9. **Inject `BenchmarkRepository` into `ProviderSelector`** (or make it queryable).
10. **Add benchmark-aware branch to `_quality_score()`**:
    ```python
    if self.flags.is_enabled("benchmark_auto_quality"):
        scores = self.benchmark_repo.avg_scores(provider)
        return scores.get("avg_quality_auto", 0.3)
    ```
11. Default `benchmark_auto_quality` to `True` after integration stabilizes.

### Total Estimated Effort: 5-7 days
