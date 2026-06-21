# Sprint 5.5 Cleanup Review

Generated: 2026-06-21
Commit: 8b83aaa

## 1. Keep

These components are clean and require no action.

| Component | Status | Notes |
|-----------|--------|-------|
| Feature flags | Clean | All checks use `FeatureFlags.is_enabled()`. No string literal duplication. |
| Migrations runner | Clean | All 5 migrations properly tracked, idempotent, no orphans. |
| Port/adapter pattern | Clean | Properly wired through dependency injection. |
| Application services | Clean | `CarouselService`, `ReportService`, `PresentationService`, `ResearchService`, `ArtifactService`, `OpenDesignService` all functional. |
| Renderers (except CodeRenderer) | Clean | Each renderer serves its purpose. PreviewRenderer and dedicated renderers are complementary, not duplicative. |
| MemoryGraph | Clean | 5 memory types, importance scoring, recency tracking, feedback learning. |
| WorkspaceManager | Clean | Brand/University/Project with semester support and active state. |
| ContextEngine | Clean | Workspace-aware retrieval with tiered importance. |
| Planner | Clean | 25 intents, 3 modes, Arabic+English keywords. |
| WorkflowEngine | Clean | Handler registration, approval gating, status state machine. |
| ConnectionManager | Clean | Thread-safe SQLite with WAL mode. |
| ConversationStore | Clean | CRUD with workspace filtering. |
| ProviderRegistry | Clean | Three registered providers (opencode, ollama, duckduckgo). |
| Storage | Clean | Config, usage, history via SQLite. |
| Limiter | Clean | Daily rate limiting per provider. |
| All 42 test files | Clean | Valid tests, none unused. |
| VISION.md | Clean | Still accurate. |

## 2. Refactor

These items have known issues that should be fixed.

### 2.1 Provider Selection Gap — Critical

**Files**: `toll/core/ai.py`, `toll/core/provider_selector.py`, all application services

**Problem**: Each application service calls `self.selector.select(ArtifactType.CAROUSEL)` to pick a provider, then immediately calls `self.ai.ask(prompt)` which **ignores the selection** and tries all providers in arbitrary order. The `ProviderSelector` result is completely unused.

**Fix**: Add an optional `provider_name` parameter to `AI.ask()`:

```python
class AI:
    def ask(self, prompt: str, system: str = "", provider_name: str | None = None) -> str:
        if provider_name:
            provider = self.registry.get_llm(provider_name)
            if provider and self.limiter.can_use(provider_name):
                return provider.ask(prompt, system).content
        # fall through to existing fallback logic
```

Then pass the selector result from each service:
```python
provider_name = self.selector.select(artifact_type)
raw = self.ai.ask(prompt, provider_name=provider_name)
```

### 2.2 Settings Bypass — Medium

**Files**: `toll/core/limiter.py`, `toll/core/feature_flags.py`

**Problem**: `Limiter` and `FeatureFlags` read/write the `config` table directly via SQL instead of going through the `Settings` class. This means environment variable overrides (e.g., `TOLL_DAILY_LIMIT_OPENCODE`) are not respected by the limiter or feature flag system.

**Fix**: Inject `Settings` into both classes or have `Settings` expose a unified read path that respects env var precedence.

### 2.3 Hardcoded String Literals Should Use ArtifactType Enum — Medium

**Files**: `toll/application/carousel_service.py`, `toll/application/report_service.py`, `toll/application/presentation_service.py`, `toll/application/research_service.py`

**Problem**: These files use strings like `"carousel"`, `"report"`, `"presentation"`, `"research"` in `plan.get("intent", "carousel")`, `intent="carousel"`, and `"type": "carousel"` instead of referencing `ArtifactType.CAROUSEL.value`.

**Fix**: Replace with enum references:
- `plan.get("intent", ArtifactType.CAROUSEL.value)`
- `intent=ArtifactType.CAROUSEL.value`
- `"type": ArtifactType.CAROUSEL.value`

### 2.4 Frontend-Backend API Contract — Medium

**Files**: `web/index.html`, `api/routers/workspaces.py`, `api/routers/conversations.py`

**Problem**: 6 path mismatches between frontend calls and backend routes:

| Frontend Call | Actual API | Fix |
|---------------|------------|-----|
| `GET /api/workspaces/active` | `GET /api/workspace/active` | Change frontend to `/api/workspace/active` |
| `POST /api/workspaces/active` | `POST /api/workspace/active` | Change frontend to `/api/workspace/active` |
| `GET /api/workspaces/{id}/semesters` | `GET /api/semesters/{id}` | Change frontend or add route |
| `POST /api/workspaces/{id}/semesters` | `POST /api/semesters` | Change frontend or add route |
| `GET /api/conversations/{id}/messages` | Does not exist | Add endpoint or fix frontend to use `GET /api/conversations/{id}` |
| `POST /api/conversations/{id}/messages` | Does not exist | Add endpoint or fix frontend |

### 2.5 Unused Imports — Low

| File | Unused Import |
|------|---------------|
| `api/routers/engine.py` | `Request`, `ProviderRegistry` |
| `api/routers/planner.py` | `Request`, `PlannerMode` |
| `api/main.py` | `HealthCheckError` |
| `toll/application/handler_registry.py` | `ArtifactType` |
| `toll/application/carousel_service.py` | `import json`, `from datetime import datetime, timezone` |
| `toll/application/research_service.py` | `CitationStyle` |
| `toll/engine/reports.py` | `from pathlib import Path` |
| `bot/telegram.py` | `Storage` |

### 2.6 WorkflowStatus / ArtifactStatus Shared Strings — Low

`WorkflowStatus` and `ArtifactStatus` both define `COMPLETED = "completed"` and `FAILED = "failed"`. While they model different domains, shared string values can cause confusion. Rename to e.g. `WORKFLOW_COMPLETED` / `ARTIFACT_COMPLETED` or add docstrings.

### 2.7 Missing `toll/model/__init__.py` — Low

No package init exists for `toll/model/`. This works (namespace packages in Python 3.3+) but is inconsistent with every other package having one.

## 3. Remove

These items are safe to delete with no functional impact.

### 3.1 Legacy Schema — No Impact

**File**: `toll/model/schema.sql` (26 lines)

**Reason**: Identical to `migrations/0001_initial.sql`. Never referenced anywhere in the codebase. Migration runner only globs `[0-9][0-9][0-9][0-9]_*.sql`.

**Action**: Delete file.

### 3.2 Dead Module — No Impact

**File**: `toll/core/browser.py` (17 lines)

**Reason**: Placeholder `BrowserAI` class with all methods raising `NotImplementedError`. Never imported by any file. The only references to "browser" are config keys (`daily_limit_browser`) and test data.

**Action**: Delete file. The config keys can remain (they default to `False` for browser rate limiting and are harmless).

### 3.3 Dead Directory — No Impact

**Directory**: `toll/adapters/persistence/` (1 empty `__init__.py`)

**Reason**: Empty directory, never imported. Actual persistence is in `toll/core/storage.py`.

**Action**: Delete directory and its `__init__.py`.

### 3.4 Stale Test Data — Optional Cleanup

**Directory**: `data/artifacts/*/` (17 UUID directories)

**Reason**: Generated during Sprint 4 and Sprint 5A development. Not referenced by any test assertions. The artifact system creates directories on demand.

**Action**: Delete contents of `data/artifacts/` (keep directory itself). Can also delete `data/artifacts/archive/`.

### 3.5 CodeRenderer (Unused in Production) — Keep, but note

**File**: `toll/engine/renderers/code_renderer.py`

**Status**: Only used in `tests/engine/test_renderers.py`. No application service instantiates `CodeRenderer`. The `handler_registry.py` does not register a code handler.

**Action**: No action needed if code generation is planned. If not, delete.

## 4. Deferred

These items are recognized but deferred to future sprints.

### 4.1 Legacy Engine Endpoints

**Endpoints**: `POST /api/content`, `POST /api/report`, `POST /api/present`

**Status**: Redundant with `/api/chat` (which uses planner + workflow engine + application services). However, they are still called by:
- `cli/main.py` — uses `ContentMachine`, `Reports`, `PromptGenerator` directly
- `bot/telegram.py` — uses `ContentMachine`, `Reports`, `PromptGenerator` directly

**Deferred until**: CLI and Telegram bot are refactored to use application services via the planner/workflow pipeline. Sprint 5.5 is codebase cleanup only — no consumer migration.

### 4.2 CLI Migration

**Files**: `cli/main.py`

**Status**: Uses legacy `ContentMachine`, `Reports`, `PromptGenerator` with standalone constructors (no DI, no ConnectionManager). Does not use artifact system, planner, or workflow engine.

**Deferred until**: Sprint 6 or later when CLI is rewritten to use application services.

### 4.3 Telegram Bot

**File**: `bot/telegram.py`

**Status**: Orphaned module. Not connected to any entry point (`main()` is only gated behind `if __name__ == "__main__"`). Uses legacy classes. Unused import of `Storage`. No `__init__.py`.

**Deferred until**: Telegram integration is explicitly planned. Not in scope for Sprint 5.5.

### 4.4 Documentation Drift

**Files**: `TODO.md`, `ARCHITECTURE.md`

**Issues**:
- `TODO.md`: Sprint 4 and Sprint 5 checklist items marked as `⬜ Pending` despite being fully implemented.
- `ARCHITECTURE.md`: Lists Artifact System as dormant Layer 2 (off by default) but it is live and enabled. Lists Browser as a supported provider but it is a stub. Missing ConnectionManager, ContextEngine, Research Layer entirely.

**Deferred until**: After Sprint 5.5 code changes are complete — update docs to reflect final state.

### 4.5 Web Dashboard Rewrite

**Status**: The dashboard at `web/index.html` doesn't expose most API functionality (23 endpoints never called from frontend). Has 6 broken path mappings.

**Deferred until**: Sprint 6 or later when frontend is rewritten to use all available API endpoints.

### 4.6 Duplicate Status Values

`WorkflowStatus` and `ArtifactStatus` both define `COMPLETED = "completed"` and `FAILED = "failed"`. Low priority — not causing bugs but worth noting.

## Summary Table

| # | Item | Category | Effort | Impact | Priority |
|---|------|----------|--------|--------|----------|
| 2.1 | Provider selection gap | Refactor | Small | Medium | High |
| 3.1 | Delete `schema.sql` | Remove | Trivial | None | High |
| 3.2 | Delete `browser.py` | Remove | Trivial | None | High |
| 3.3 | Delete `persistence/` | Remove | Trivial | None | High |
| 2.5 | Unused imports | Refactor | Small | None | Medium |
| 2.3 | Hardcoded strings → enums | Refactor | Small | Low | Medium |
| 2.2 | Settings bypass | Refactor | Medium | Medium | Medium |
| 2.4 | Frontend API paths | Refactor | Medium | Medium | Medium |
| 2.6 | Status shared strings | Refactor | Trivial | None | Low |
| 2.7 | Missing `model/__init__.py` | Refactor | Trivial | None | Low |
| 3.4 | Stale test data | Remove | Small | None | Low |
| 3.5 | CodeRenderer unused | Note | None | None | Low |
| 4.1 | Legacy endpoints | Deferred | — | — | — |
| 4.2 | CLI migration | Deferred | — | — | — |
| 4.3 | Telegram bot | Deferred | — | — | — |
| 4.4 | Documentation drift | Deferred | — | — | — |
| 4.5 | Web dashboard | Deferred | — | — | — |
