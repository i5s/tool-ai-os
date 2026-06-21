# Sprint 3.5 Report — Code Architecture & Workflow Resilience

**Goal**: Centralize DB access, eliminate phantom auto-execute workflows, fix plan-only dead ends, and harden recovery after unexpected shutdown.

**Dates**:
- Plan approved: 2026-06-21
- Implementation: 2026-06-21
- 92 tests passing, 0 failing

---

## Changes

### 1. `ConnectionManager` — new central DB access layer

**File**: `toll/core/connection_manager.py` (new, 96 lines)

- Wraps `sqlite3.connect` with WAL mode + foreign keys enabled
- Provides `.execute()`, `.executemany()`, `.executescript()`, `.commit()`, `.close()`, and `.health_check()`
- Runs all pending migrations on init
- `health_check()` runs `PRAGMA foreign_keys` to verify the connection is alive

### 2. All components refactored to use `ConnectionManager`

| Component | Before | After |
|---|---|---|
| `Storage` | `sqlite3.connect(path)` in constructor | Accepts `ConnectionManager` |
| `FeatureFlags` | inline `sqlite3.connect()` | Accepts `ConnectionManager` |
| `ConversationStore` | inline `sqlite3.connect()` | Accepts `ConnectionManager` |
| `MemoryGraph` | inline `sqlite3.connect()` | Accepts `ConnectionManager` |
| `WorkspaceManager` | inline `sqlite3.connect()` | Accepts `ConnectionManager` |
| `ContextEngine` | inline `sqlite3.connect()` | Accepts `ConnectionManager` |
| `WorkflowEngine` | inline `sqlite3.connect()` | Accepts `ConnectionManager` |

### 3. API layer updated

- **New dependency**: `get_connection_manager()` — lifespan-scoped singleton
- `plan/approve/reject/run` endpoints use `get_connection_manager` directly
- Status endpoint uses `cm.health_check()` to report DB health

### 4. Intent detection consolidated into Planner

- **Removed** `toll/planner/detect.py` (the standalone `detect_type()` function)
- Planner now owns all intent detection via keyword matching + disambiguation
- **New `search` intent**: Arabic (`ابحث عن`, `بحث عن`, `بحث`) and English (`search`, `google`) keywords
- Disambiguation rules: longest keyword match wins; Arabic keyword count breaks ties

### 5. Workflow engine fixes

- **`create()`**: plan-only plans → `PENDING` (no auto-run). Added `can_auto_execute` field on `Plan` domain object
- **`create_and_run()`**: new method that creates and immediately runs workflows without double-creation
- **Plan-only dead-end fix**: `/plan` endpoint now creates a workflow + calls `run` directly
- **Phantom auto-execute fix**: `create_and_run` replaced the old pattern that was calling `create()` twice
- **`recover()`**: new method marks any `RUNNING` workflows as `FAILED` on startup

### 6. Test coverage

- **New tests**: `test_connection_manager.py` (10 tests — WAL, FKs, health, concurrent execute, migrations, close/reopen, executescript)
- **Extended**: `test_planner.py` — 6 new tests covering search intent, disambiguation, Arabic preference, fallback
- **Updated**: all component tests use `ConnectionManager` fixture; 73 tests refactored + 19 new = 92 total

---

## Files changed

| File | Action |
|---|---|
| `toll/core/connection_manager.py` | **NEW** — 96 lines |
| `toll/core/storage.py` | Refactored |
| `toll/core/feature_flags.py` | Refactored |
| `toll/core/conversation_store.py` | Refactored |
| `toll/core/memory_graph.py` | Refactored |
| `toll/core/workspace_manager.py` | Refactored |
| `toll/core/context_engine.py` | Refactored |
| `toll/workflow/engine.py` | Refactored + recover() + plan-only/phantom fix |
| `toll/planner/planner.py` | search intent + disambiguation |
| `toll/planner/detect.py` | **DELETED** |
| `api/main.py` | Updated (lifespan, dependencies) |
| `api/routers/chat.py` | Removed detect_type |
| `api/routers/plan.py` | Fixed plan-only + phantom |
| `tests/conftest.py` | New fixtures (cm, cm_session) |
| `tests/core/test_connection_manager.py` | **NEW** — 10 tests |
| `tests/core/test_planner.py` | Extended — 6 new tests |
| All other test files | Updated fixtures |

---

## How to test

```bash
pytest tests/ --ignore=tests/adapters/test_duckduckgo.py -v
```

---

## What's next (Sprint 4)

- Recovery integration: call `workflow.recover()` on startup
- Web search provider integration
- Multi-step approvals
