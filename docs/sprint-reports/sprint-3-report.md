# Sprint 3 Report — Context Engine + Planner + Workflow Engine

**Status:** ✅ Complete  
**Commit:** `36e32c2`  
**Date:** 2026-06-21  
**Tests:** 70 passing

---

## 1. Approved Adjustments Applied

Per the approved Planner Approval Matrix modifications:

| Item | Approved Rule | Implementation |
|------|---------------|----------------|
| Workspace Creation | AUTO EXECUTE | `workspace_create` → `ApprovalLevel.AUTO` |
| Workspace Deletion | REQUIRES APPROVAL | `workspace_delete` → `ApprovalLevel.APPROVAL` |
| Memory Suggestion | AUTO EXECUTE | `memory_suggest` → `ApprovalLevel.AUTO` |
| Memory Promote/Update/Delete | REQUIRES APPROVAL | `memory_promote`, `memory_update`, `memory_delete` → `ApprovalLevel.APPROVAL` |
| Feature flag | `memory_auto_learning = false` (default) | Added to `DEFAULT_FLAGS` |
| Planner modes | Strict / Balanced / Fast (default Balanced) | Implemented via `PlannerMode` enum and feature flags `planner_strict_mode`, `planner_fast_mode` |

---

## 2. Components Implemented

### 2.1 Context Engine

**File:** `toll/context/engine.py`

Builds a prompt-ready context block from:
- Active workspace state (brand / university / project / semester)
- Relevant memories from Memory Graph (`MemoryGraph.retrieve()`)
- Recent conversation history

Returns a `ContextResult` with:
- `prompt`: formatted string for the LLM
- `memories`: list of relevant memory dicts
- `active_workspace`: workspace summary dict
- `recent_messages`: truncated recent messages

### 2.2 Planner

**File:** `toll/planner/planner.py`

Classifies user intent and assigns an approval level.

**Approval levels:**
- `auto_execute`
- `plan_only`
- `requires_approval`

**Modes:**
- **Balanced** (default): uses the approved matrix directly
- **Strict**: escalates `plan_only` and state-touching `auto_execute` to `requires_approval`; read-only auto tasks stay auto
- **Fast**: downgrades `plan_only` to `auto_execute`; `requires_approval` stays gated

**Matrix coverage:**
- AUTO: questions, summaries, translation, prompt generation, brainstorming, explanations, code snippets, calculations, image analysis, chat, workspace creation, memory suggestion
- PLAN ONLY: research plans, study plans, marketing plans, content calendars, roadmaps, SWOT, competitor analysis plans
- REQUIRES APPROVAL: reports, presentations, carousels, website changes, file operations, memory write/update/delete/promote, bulk content, code file writes, email sending, publishing, migrations, settings changes, workspace deletion, image generation, PDF export, data import

### 2.3 Workflow Engine

**File:** `toll/workflow/engine.py`

Persists and executes plans through approval checkpoints.

**States:**
`pending` → `approved` / `rejected` → `running` → `completed` / `failed`

- Auto-execute plans skip `pending` and start at `approved`
- Manual approval/rejection via `approve()` / `reject()`
- Handlers are registered per intent with `register_handler(intent, callable)`
- Results and errors persisted in `workflows` table

---

## 3. API Endpoints Added

**Router:** `api/routers/planner.py`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/plan` | Classify a message and return a Plan |
| GET | `/api/plan/mode` | Get current planner mode |
| POST | `/api/plan/mode` | Set planner mode (`strict`, `balanced`, `fast`) |
| POST | `/api/workflows` | Create a workflow from a message |
| GET | `/api/workflows` | List workflows with optional status filter |
| GET | `/api/workflows/{id}` | Get workflow details |
| POST | `/api/workflows/{id}/approve` | Approve pending workflow |
| POST | `/api/workflows/{id}/reject` | Reject pending workflow |
| POST | `/api/workflows/{id}/run` | Execute approved workflow |

**Modified:** `api/routers/engine.py` (`POST /api/chat`)
- Uses `ContextEngine` for generic chat prompts
- Uses `Planner` to classify intent
- Returns `type: "plan"` for plan-only requests
- Returns `type: "approval_required"` + `workflow_id` for approval-gated requests
- Persists user and assistant messages via `ConversationStore`

---

## 4. Database Migrations Added

- `toll/model/migrations/0003_workflows.sql`
  - Creates `workflows` table for plan execution state
  - Indexes on `status` and `updated_at`

---

## 5. Feature Flag Updates

`DEFAULT_FLAGS` in `toll/core/feature_flags.py` now includes:
- `memory_auto_learning`: `False`
- `planner_strict_mode`: `False`
- `planner_fast_mode`: `False`

When both strict and fast flags are disabled, the planner defaults to **Balanced** mode.

---

## 6. Test Coverage

**New test files:**
- `tests/core/test_context_engine.py` — workspace/memory inclusion, recent messages, limit behavior
- `tests/core/test_planner.py` — intent classification, approval levels, mode behavior
- `tests/core/test_workflow_engine.py` — create, approve, reject, run, list, state transitions

**Total:** 70 tests passing (21 new + 49 existing)

---

## 7. Files Changed

**Created:**
- `toll/context/engine.py`
- `toll/planner/planner.py`
- `toll/workflow/engine.py`
- `api/routers/planner.py`
- `toll/model/migrations/0003_workflows.sql`
- `tests/core/test_context_engine.py`
- `tests/core/test_planner.py`
- `tests/core/test_workflow_engine.py`
- `docs/sprint-reports/sprint-3-report.md`

**Modified:**
- `toll/core/feature_flags.py` — added `memory_auto_learning`, planner mode flags
- `api/main.py` — wired planner router
- `api/routers/engine.py` — integrated Context Engine and Planner into `/api/chat`
- `TODO.md` — marked Sprint 3 complete

---

## 8. Architecture Notes

- The Context Engine does **not** mutate memory; it only reads via `MemoryGraph.retrieve()`.
- The Planner is stateless; mode is driven by feature flags stored in the config table.
- The Workflow Engine owns persistence and is the single source of truth for approval state.
- `/api/chat` is now the integration point: it classifies, gates, and either responds, plans, or requests approval.

---

## 9. Known Limitations / Next Steps

- **Dashboard approval UI:** The web dashboard does not yet render approval cards or plan-only previews. API endpoints are ready.
- **Workflow handlers:** Only intent-level handler registration exists; concrete execution handlers for each approved intent belong in Sprint 4 (Application Services).
- **Memory auto-learning:** Feature flag added but not wired. When enabled, the Context Engine / chat layer should suggest memories from conversations automatically.
- **Plan/approval chat UI:** `/api/chat` returns `type: "approval_required"` and `type: "plan"`, but the frontend currently treats all responses as plain text.

---

## 10. Decision Records

| Decision | Rationale |
|----------|-----------|
| Planner modes via feature flags | Keeps settings centralized and user-configurable without a separate settings table |
| Strict mode keeps read-only auto tasks as AUTO | Prevents over-gating simple Q&A while still catching stateful actions |
| Fast mode does not downgrade APPROVAL | Safety floor: reports, file ops, memory mutations always require approval |
| Workflow auto-starts at APPROVED for AUTO plans | Reduces state-machine friction for safe actions |

---

**Sprint 3 is complete and approved for closure. Sprint 4 is not started.**
