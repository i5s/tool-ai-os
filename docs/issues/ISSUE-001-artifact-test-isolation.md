# ISSUE-001: Artifact Test Isolation Bug

> **Status**: Open — known pre-existing issue (pre-Sprint X)
> **Severity**: Low (test-only, no production impact)
> **Discovered**: Sprint X Foundation Audit

---

## Description

`test_list_artifacts_empty` in `tests/api/test_artifacts_api.py` fails because the artifact test suite shares a database connection with other test suites (chat, research) that create artifacts. By the time the artifact tests run, the database already contains artifacts from previous tests, causing the "list should be empty" assertion to fail.

## Root Cause

The artifact API tests use the **default application database path** (`DB_PATH`) instead of an isolated temporary database (`tmp_path`). Tests in `test_chat_api.py` and `test_research_memory_api.py` create research artifacts that persist in the same database, contaminating the artifact test's empty-list expectation.

Compare with the Sprint X test suites (agents, shared_memory, tasks), which use `tmp_path` fixtures correctly and never exhibit this issue:

```python
# Sprint X pattern — isolated per-test database
@pytest.fixture
def temp_db_path(tmp_path):
    return tmp_path / "test.db"

@pytest.fixture
def cm(temp_db_path):
    mgr = ConnectionManager(db_path=temp_db_path)
    yield mgr
    mgr.close()
```

## Reproduction

```bash
# Run artifact tests after chat tests — will fail:
.venv/bin/python -m pytest tests/api/ -v --tb=short -k "test_list_artifacts_empty"

# Run artifact tests in isolation — will pass:
.venv/bin/python -m pytest tests/api/test_artifacts_api.py -v --tb=short
```

## Impact

- **1 failing test** (`test_list_artifacts_empty`) when running the full test suite.
- **No production impact** — purely a test infrastructure issue.
- Prevents green CI pipeline runs.

## Fix

Refactor `tests/api/test_artifacts_api.py` to use `tmp_path`-based database isolation, following the same pattern used by `tests/agents/test_agents.py`:

1. Add a `temp_db_path` fixture using `tmp_path`
2. Add a `cm` fixture injecting `ConnectionManager` via `dependency_overrides`
3. Ensure all 5 artifact tests reference the isolated `cm` fixture

## Workaround

Run artifact tests in isolation against a fresh temporary database until fixture isolation is implemented.

## Remediation Plan

| Step | Description | Est. |
|------|-------------|------|
| 1 | Add `tmp_path` fixture to `tests/api/test_artifacts_api.py` | 5 min |
| 2 | Inject `ConnectionManager` override into `app.dependency_overrides` | 5 min |
| 3 | Verify all 5 artifact tests pass in isolation | 5 min |

**Total estimate**: 15 minutes
