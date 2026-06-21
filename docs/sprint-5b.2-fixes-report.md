# Sprint 5B.2 — Recommended Findings Fixes

> Date: 2026-06-21  
> Based on v0.6 Architecture Audit

---

## Findings Fixed

### 1. XSS — `innerHTML` Injection (R7)

| Severity | File | Change |
|----------|------|--------|
| Recommended | `web/index.html:1421` | `resultDiv.innerHTML = data.answer` → `resultDiv.textContent = data.answer` |

AI query response was injected as raw HTML with no sanitization. The system prompt generates Arabic text, but nothing prevents the AI from producing `<script>`, `<img onerror>`, or `<iframe>` tags. Changed to `textContent` which safely escapes all HTML.

**O5/O8 (Optional):** Inline event handlers use server-generated UUIDs (`s.id`) which are not user-controllable; `escHtml()` already wraps all user-visible text. SVG-as-`<img>` does not execute scripts. These are not actionable and have been removed from the active finding list.

---

### 2. Missing 404 Responses (R6)

| Severity | File | Change |
|----------|------|--------|
| Recommended | `api/routers/notebooks.py` | Added 6 resource-existence checks |

**Endpoints fixed:**
| Endpoint | Before | After |
|----------|--------|-------|
| `GET .../sources` | Returned `{"sources":[]}` for missing notebook | Returns 404 |
| `GET .../notes` | Same | Returns 404 |
| `GET .../snapshots` | Same | Returns 404 |
| `DELETE .../sources/{id}` | Always `{"success":True}` | Returns 404 if source not found |
| `DELETE .../notes/{id}` | Always `{"success":True}` | Returns 404 if note not found |
| `DELETE .../snapshots/{id}` | Always `{"success":True}` | Returns 404 if snapshot not found |

**Service changes:** `delete_source()`, `delete_note()`, `delete_snapshot()` now check `cursor.rowcount` and return `False` if no rows were affected (was always `True`).

---

### 3. `asyncio.run()` in Running Event Loop (R5)

| Severity | File | Change |
|----------|------|--------|
| Recommended | `toll/core/ai.py` | Added `_run_async()` safe wrapper |

`asyncio.run()` raises `RuntimeError` if called from a thread with a running event loop. Replaced 3 calls (`AI.ask()` × 2, `AI.search()`) with `_run_async()` which:
1. Tries `asyncio.get_running_loop()` to detect existing event loop
2. No loop → uses `asyncio.run()` (existing behavior)
3. Loop exists → dispatches to a `ThreadPoolExecutor` thread that calls `asyncio.run()` in its own loop

This is the standard pattern used by `httpx` and similar libraries to bridge sync/async.

---

### 4. FTS5 Dead/Broken Index (R1, R2, R3)

| Severity | File | Change |
|----------|------|--------|
| Recommended | Multiple | Removed FTS5 table and dead code |

**Problems found:**
- **R1:** `content_rowid='rowid'` expects integer rowids synced to `notebook_notes`, but the TEXT PK means auto-assigned FTS rowids don't correspond to any UUID
- **R2:** Index was write-only — `_index_notes()` inserted rows, but no code ever queried `notebook_notes_fts`
- **R3:** No cleanup on note deletion — orphaned FTS rows accumulated silently

**Fixes:**
| File | Change |
|------|--------|
| `toll/model/migrations/0008_drop_notebook_fts.sql` | New migration: `DROP TABLE IF EXISTS notebook_notes_fts` |
| `toll/application/notebook_service.py:225` | Removed call to `self._index_notes(notes)` |
| `toll/application/notebook_service.py:389-398` | Removed `_index_notes()` method entirely |

---

### 5. NotebookLM Test Coverage (R10, R11)

| Severity | File | Tests Added |
|----------|------|-------------|
| Recommended | 3 test files | 40 new tests |

| Test File | Tests | Coverage Area |
|-----------|-------|---------------|
| `tests/application/test_notebook_service.py` | 18 | CRUD, source content persistence, delete-returns-false, query edge cases, snapshot creation |
| `tests/api/test_notebooks_api.py` | 19 | All 15 endpoints + 404/403/400 edge cases, flag-gating |
| `tests/application/test_handler_registry.py` | 4 (was 1) | Notebook handler registration, conditional gating, dispatch correctness |

Collectively, these cover the previously untested `notebook_service.py`, `notebooks.py` router, and the `notebooklm_enabled` branch of `handler_registry.py`.

---

### 6. Low-Risk Items

| Audit ID | File | Change |
|----------|------|--------|
| O1 | `toll/ports/notebook.py` | `snapshot_data: dict` → `snapshot_data: dict = field(default_factory=dict)` |
| O6 | `api/routers/notebooks.py:358` | Removed redundant `FeatureFlags(cm=cm)` — uses `svc.flags` instead |
| O9 | `toll/adapters/notebooks/notebooklm.py` | Removed unused `self.cm` from `__init__` |
| O12 | `toll/adapters/notebooks/notebooklm.py` | `provider: NotebookLMProvider` → `provider: NotebookLMProvider \| None = None` |
| O18 | `toll/model/__init__.py` | Created empty `__init__.py` to make it an explicit package |

**O2/O4 deferred:** Date defaults (`""` → `None`) and `alert()` → toast migration would touch many files with narrower safety margin. Marked as future polish.

---

## Files Changed

| File | Type | Lines Changed | Status |
|------|------|---------------|--------|
| `toll/model/migrations/0007_notebook_source_content.sql` | New | 3 | Created (Sprint 5C fix) |
| `toll/model/migrations/0008_drop_notebook_fts.sql` | New | 5 | Created |
| `toll/model/__init__.py` | New | 0 | Created |
| `toll/ports/notebook.py` | Edited | 2 lines | O1 fix |
| `toll/core/ai.py` | Edited | +8/-5 | R5 fix |
| `toll/application/notebook_service.py` | Edited | +3/-17 | C3 inserts, rowcount checks, FTS5 removal |
| `toll/adapters/notebooks/notebooklm.py` | Edited | 3 lines | O9, O12 |
| `toll/application/handler_registry.py` | Edited | 12 lines | C2 wrapper fix |
| `api/routers/notebooks.py` | Edited | +16/-6 | R6 404 checks, O6 flag dedup |
| `web/index.html` | Edited | 1 line | R7 XSS fix |
| `tests/application/test_notebook_service.py` | New | 95 | 18 tests |
| `tests/api/test_notebooks_api.py` | New | 130 | 19 tests |
| `tests/application/test_handler_registry.py` | Rewritten | 49 | 4 tests (was 1) |

---

## Test Impact

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Total tests | 170 | 210 | **+40** |
| Skipped | 2 | 2 | 0 |
| Notebook service tests | 0 | 18 | **+18** |
| Notebook API tests | 0 | 19 | **+19** |
| Handler registry tests | 1 | 4 | **+3** |
| Notebook coverage areas | 0% | Service+API+Handler | New modules |

---

## Remaining Findings from v0.6 Audit

After this sprint, the following findings remain:

### Critical
| ID | Finding | Reason Deferred |
|----|---------|-----------------|
| — | None | All 3 criticals fixed in Sprint 5B.2 (C1, C2, C3) |

### Recommended
| ID | Finding | Reason Deferred |
|----|---------|-----------------|
| R4 | FTS5 ↔ MemoryGraph cross-reference | Moot — FTS5 index removed; flag name `notebooklm_memory_index` is now a no-op. Needs a design decision (rename flag or integrate with MemoryGraph) |
| — | None remaining from R1-R3, R5-R7, R10-R11 | All fixed |

### Optional
| ID | Finding | Notes |
|----|---------|-------|
| O2 | `created_at` defaults `""` instead of `None` | Low risk; consistent with existing codebase |
| O3 | `nbState` separate from main `state` | Cosmetic; would need JS refactor |
| O4 | 15 `alert()` calls | Needs toast system — out of scope for "no new features" |
| O7 | Response format inconsistency | Backward-compatible; breaking change on purpose |
| O8 | SVG in `<img>` via file upload | `<img>` tags do not execute SVG scripts — not a real XSS vector |
| O10 | `NotebookLMResearchAdapter` adapter dead code | Unused since `research_service.py` constructs sources directly |
| O11 | Notebook sources classified `language="en"` | Arabic-first; affects citation formatting |
| O13 | MemoryGraph has no abstract port | Design decision for future Sprint |
| O14 | `AI()` creates non-shared Registry/Limiter | Architectural; needs refactoring |
| O15 | Unmatched workflow intent completes as success | Workflow design choice |
| O16 | Snapshot/delete/audio not registered as handlers | Feature completeness for Sprint 5C |
| O17 | Hardcoded provider names in `Limiter.status()` | Maintenance; low impact |
| O19 | `toll/ports/repository.py` orphaned | Dead code; cleanup |
