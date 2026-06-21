# Sprint 3.5 — Storage and Reliability Hardening

**Status:** Draft (pending approval)  
**Sprint Goal:** Fix foundational infrastructure issues identified in the Architecture Audit before adding new features.

---

## Work Items

### A. ConnectionManager — Centralized SQLite Connection (Goals 1–5)

#### A.1 Create `toll/core/connection_manager.py`

```python
class ConnectionManager:
    """Owns a single SQLite connection. Thread-safe. Sets WAL + FK pragmas."""

    def __init__(self, db_path: Path): ...
    def execute(self, sql, params=()) -> sqlite3.Cursor: ...
    def executemany(self, sql, seq): ...
    def executescript(self, sql): ...
    def commit(self): ...
    def close(self): ...
    @property
    def connection(self) -> sqlite3.Connection: ...
```

- Opens connection with `check_same_thread=False` (single-user local-first trade-off)
- Sets `PRAGMA journal_mode=WAL`
- Sets `PRAGMA foreign_keys = ON`
- Runs `MigrationRunner.migrate()` exactly once
- Wraps all writes in `threading.Lock` for thread safety
- Provides `execute()` convenience that delegates to `conn.execute()` (reads) or locks+writes

#### A.2 Refactor `toll/core/storage.py`

- `Storage.__init__(cm: ConnectionManager)` — accepts a `ConnectionManager` instead of `db_path`
- Remove `Storage._migrate()` — migrations are now the ConnectionManager's responsibility
- Remove `Storage.conn` — uses `cm.connection` or `cm.execute()` instead
- All existing methods delegate to `self.cm` for all DB operations
- Old `Storage(db_path=...)` pattern becomes `Storage(cm=...)`

#### A.3 Update all component constructors

Every component that currently does `self.db = storage or Storage()` must accept a `ConnectionManager`:

| Component | Current | New |
|---|---|---|
| `FeatureFlags` | `storage: Storage \| None = None` | `cm: ConnectionManager` |
| `ConversationStore` | `storage: Storage \| None = None` | `cm: ConnectionManager` |
| `MemoryGraph` | `storage: Storage \| None = None` | `cm: ConnectionManager` |
| `WorkspaceManager` | `storage: Storage \| None = None` | `cm: ConnectionManager` |
| `WorkflowEngine` | `storage: Storage \| None = None` | `cm: ConnectionManager` |
| `ContextEngine` | `storage: Storage \| None = None` | `cm: ConnectionManager` |

Each component stores `self.cm` and uses `self.cm.execute()` or `self.cm.connection` for all DB operations.  
`Storage` remains available as a thin adapter for code that calls `.conn` directly.

#### A.4 FastAPI lifespan + dependency injection

```python
# api/main.py — lifespan replaces global app
@asynccontextmanager
async def lifespan(app: FastAPI):
    cm = ConnectionManager(DB_PATH)
    app.state.cm = cm
    yield
    cm.close()

# api/dependencies.py
def get_connection_manager(request: Request) -> ConnectionManager:
    return request.app.state.cm
```

All routers receive `ConnectionManager` via `Depends(get_connection_manager)` and pass it to component constructors.

#### A.5 Update tests

- `tests/conftest.py` fixture creates `ConnectionManager(tmp_path / "test.db")` with WAL + FKs enabled
- All test fixtures replace `Storage()` with `ConnectionManager()` for their components
- `Storage` still tested because it wraps a `ConnectionManager`

#### A.6 Migration Impact

- **No new `.sql` migration file.** WAL and FK are connection pragmas, not schema changes.
- WAL mode creates `-wal` and `-shm` sidecar files alongside the `.db` file. Users backing up the database must copy all three files.

---

### B. Workflow Recovery After Restart (Goal 6)

#### B.1 Add `WorkflowEngine.recover()` (e6a4263)

```python
def recover(self) -> list[Workflow]:
    """Mark running workflows as failed after unexpected shutdown.
    Approved and pending workflows are left untouched."""
```

- Scans for workflows in `running` status
- Sets status to `failed`, error to `"Server restart interrupted execution"`
- Returns list of recovered (failed) workflows
- Does NOT touch `approved` or `pending` workflows

#### B.2 Default handler registration at startup

- Move handler registration from runtime code to `main.py` startup
- Register a fallback handler that delegates to AI for unknown intents
- Intent-specific handlers registered at startup (research_plan, report, etc.)

#### B.3 Startup hook

- `lifespan` in `main.py` calls `engine.recover()` after creating ConnectionManager
- Recovery logs affected workflow IDs
- Handlers are registered before `recover()` runs so approved workflows can execute

---

### C. Fix Plan-Only Dead Ends (Goal 7)

#### C.1 Plan-only creates a workflow

`/api/chat` currently returns plan text and stops. New behavior:

- Plan-only intents create a workflow via `WorkflowEngine.create()`
- Workflow auto-approves and auto-runs (like AUTO but goes through the engine)
- Handler for plan-only intents returns the plan description as the result
- Workflow completes
- Response includes `workflow_id` and the plan result

#### C.2 Frontend integration

- Response format: `{ "type": "plan", "workflow_id": "...", "plan": {...}, "response": "..." }`
- User can reference `workflow_id` to say "execute this plan" (future: Sprint 4 follow-up execution)

#### C.3 Migration Impact

- No schema changes. Plan-only workflows re-use the existing `workflows` table.
- Existing plan-only responses from previous conversations are not retroactively converted.

---

### D. Fix Auto-Execute Phantom Workflows (Goal 8)

#### D.1 Chat handler: AUTO tasks don't create workflows

Current: auto-execute path in `/api/chat` only routes to task handlers, no workflow involved. This is correct — keep it.

#### D.2 `/api/workflows` endpoint: auto-execute completes the lifecycle

Current `POST /api/workflows` creates a workflow, sets `can_auto_execute=True` → status APPROVED → never calls `run()`.

Fix: after `create()`, immediately inspect `can_auto_execute`. If true, call `run()`. Return the completed workflow result.

---

### E. Intent Detection Cleanup (Goal 9)

#### E.1 Remove `detect_type()` from `api/routers/engine.py`

The `detect_type()` function duplicates `Planner._detect_intent()`. Remove it entirely.

Chat handler task routing switches from `detect_type()` keywords to `plan.intent` from the Planner.

| Old `task_type` | New `plan.intent` |
|---|---|
| `report` | `report` |
| `research` | `research_plan` (PLAN_ONLY) → needs handler |
| `search` | stays in chat handler (no Planner intent for search) |
| `present` | `presentation` |
| `prompt` | `prompt_generation` |
| `carousel` | `carousel` |
| `code` | `code_snippet` |
| `auto` (fallback) | `chat` + Context Engine |

#### E.2 Add disambiguation to `Planner._detect_intent()`

Current scoring: sum of keyword hits, ties broken by dict iteration order (arbitrary).

Fix:
- Break ties by choosing the intent with the longest keyword match
- If still tied, prefer the intent with more Arabic keywords matched
- If still tied, prefer the first in the matrix
- Add test coverage for ambiguous messages

#### E.3 Steps cleanup

Remove `Planner._steps_for()` from API responses. Steps are currently hardcoded wallpaper. Remove from the `Plan` dataclass, or leave as empty list.

#### E.4 Migration Impact

- Removing `detect_type()` means the chat handler no longer has a `search` keyword path. Search must be mapped to a Planner intent or handled as a special case.
- `research` type currently goes to AI for a full research paper. After change, `research_plan` is PLAN_ONLY (produces a plan, not a paper). This changes behavior — need a separate `research_execute` intent for executing a research write, or handle this in the planner.

---

## Migration Impact Analysis

| Migration | Impact |
|---|---|
| `0001_initial.sql` | Unchanged. FK constraints in schema (`messages.conversation_id`) become active for the first time. |
| `0002_memory_graph.sql` | Unchanged. FK constraint (`semesters.university_id`) becomes active. |
| `0003_workflows.sql` | Unchanged. |
| New migration needed? | **None.** WAL + FK are connection pragmas, not schema changes. |
| Data integrity risk | Existing orphaned rows (messages with deleted conversation_id, semesters with deleted university_id) will cause `DELETE` failures if CASCADE encounters them. Mitigation: add explicit cleanup in a startup script or ignore (FK is only checked on writes, not reads). |

### FK Activation Side Effects

- `DELETE FROM conversations WHERE id = ?` will now cascade-delete messages (desired, previously broken)
- `DELETE FROM workspaces WHERE id = ?` referencing a university with semesters will cascade-delete semesters (desired, previously broken)
- Existing orphan rows: messages pointing to missing conversations, semesters pointing to missing universities. These are valid for reads but `INSERT/UPDATE` on the parent schema won't be affected. `DELETE CASCADE` still works because it only deletes children of the deleted parent.

### WAL Mode Side Effects

- Creates `toll.db-wal` and `toll.db-shm` sidecar files in the data directory
- On clean shutdown, WAL is checkpointed and sidecar files are removed
- Backup tools must handle these extra files
- Significant read performance improvement for concurrent reads
- Write performance improves (sequential writes batched)

---

## Risk Assessment

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| **ConnectionManager shared-state lock contention** | High | Low (single-user) | WAL mode allows concurrent reads; write lock is per-transaction, not per-query. Add timeout to lock acquisition. |
| **Missed `Storage()` instantiation during refactor** | High | Medium | Grep for all `Storage(` patterns across the codebase. CI tests catch broken imports. Feature flags test path. Nine test files to update. |
| **`check_same_thread=False` exposes race in future multi-user** | Medium | Low (V1 is single-user) | Document as a V1 trade-off. Add TODO in code. Multi-user upgrade replaces ConnectionManager with connection pool. |
| **FK activation breaks existing delete operations** | Medium | Low | CASCADE was always in schema; activation only adds what was already designed. Orphaned rows don't break reads. |
| **WAL sidecar files confuse users** | Low | Medium | Document in release notes. Add graceful shutdown in `close()` to checkpoint WAL. |
| **Removing `detect_type()` changes task routing** | Medium | Medium | `search` type has no direct Planner intent — must add one or flag as edge case. `research` type changes from full AI execution to PLAN_ONLY. |
| **Workflow recovery marks workflows as failed** | Low | Low | Only `running` workflows are touched. In V1, `run()` is synchronous, so `running` workflows = server crashed mid-execution. Recovery is correct. |
| **Plan-only workflow changes chat response format** | Low | Low | Frontend treats unknown fields gracefully. Old messages in database are not affected. |
| **Feature flags `from_flags` silent priority** | Low | Low | Add warning log when both strict and fast are enabled. Not a runtime blocker. |
| **Connection not closed on FastAPI reload (dev mode)** | Low | Medium | `lifespan` shutdown closes connection. In dev reload, old process dies without cleanup. WAL checkpoint loss possible. Mitigation: add `atexit` handler. |

---

## Test Strategy

| Area | Tests to add/update | Coverage target |
|---|---|---|
| ConnectionManager | Unit test for pragma settings, thread safety, close lifecycle | New file: `tests/core/test_connection_manager.py` |
| Storage refactor | Update existing `test_storage.py` to use ConnectionManager fixture | All existing tests pass unchanged |
| Component updates | Update conftest fixtures, all 9 component test files | Green CI |
| Workflow recovery | `recover()` marks running → failed, leaves others | `test_workflow_engine.py` |
| Plan-only workflow | Creates workflow, auto-approves, auto-runs | `test_planner.py` + `test_workflow_engine.py` |
| Auto-execute workflow | `create()` + immediate `run()` for auto-execute | `test_workflow_engine.py` |
| Intent disambiguation | Tie-breaking, Arabic priority, longest match wins | `test_planner.py` |
| FK activation | Cascade delete works for conversations→messages, workspaces→semesters | `test_storage.py` or integration |
| End-to-end | `/api/chat` with plan-only → creates workflow, AUTO → no workflow | `test_api.py` |

---

## Dependencies

- **None.** All work is internal refactoring. No new third-party packages.
- Requires re-running all migration files? **No** — already applied migrations are tracked in the `migrations` table.

---

## Files Changed (estimated)

| File | Change |
|---|---|
| `toll/core/connection_manager.py` | **NEW** |
| `toll/core/storage.py` | Refactor to accept `ConnectionManager` |
| `toll/core/feature_flags.py` | Accept `ConnectionManager` |
| `toll/core/conversations.py` | Accept `ConnectionManager` |
| `toll/memory/graph.py` | Accept `ConnectionManager` |
| `toll/workspace/manager.py` | Accept `ConnectionManager` |
| `toll/workflow/engine.py` | Accept CM + add `recover()` + fix phantom/plan-only |
| `toll/context/engine.py` | Accept `ConnectionManager` |
| `toll/planner/planner.py` | Add disambiguation, remove steps |
| `api/main.py` | Add lifespan with ConnectionManager |
| `api/dependencies.py` | Add `get_connection_manager()` |
| `api/routers/engine.py` | Remove `detect_type()`, use plan.intent, fix plan-only |
| `api/routers/planner.py` | Auto-execute fix, handler registration |
| `tests/conftest.py` | ConnectionManager fixture |
| `tests/core/test_storage.py` | Update for ConnectionManager |
| `tests/core/test_feature_flags.py` | Update fixture |
| `tests/core/test_conversation_store.py` | Update fixture |
| `tests/core/test_memory_graph.py` | Update fixture |
| `tests/core/test_workspace_manager.py` | Update fixture |
| `tests/core/test_workflow_engine.py` | Update + add recovery tests |
| `tests/core/test_context_engine.py` | Update fixture |
| `tests/core/test_planner.py` | Add disambiguation tests |
| `tests/core/test_connection_manager.py` | **NEW** |
| `tests/test_api.py` | Update for new chat routing |
| `docs/sprint-reports/sprint-3.5-plan.md` | This file |

**Total: ~25 files (2 new, 23 modified)**
