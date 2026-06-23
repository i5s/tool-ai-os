# Post-8B Architecture Plan — Sprint 9 Foundation

> **For Hermes:** Use subagent-driven-development to execute this plan task-by-task.

**Goal:** Close the remaining HIGH-priority gaps from the Sprint 7C+8 audits, unify the scattered memory/task/runtime layers, and lay a solid foundation for automation and video/audio generation without breaking the existing FastAPI + SQLite WAL stack.

**Architecture:** Consolidate memory access behind a `MemoryGateway`, reuse existing `toll/tasks/` and `toll/executions/` modules for async dispatch, drop the benchmark-flag-only behavior in favor of safe default-off toggles, and finally refresh `ARCHITECTURE.md` to reflect the real code layout rather than the 2026-01 snapshot.

**Tech Stack:** Python 3.11, FastAPI, SQLite WAL, Pydantic-friendly dataclasses, existing pytest suite.

---

## Current context / assumptions

- `.venv` with Python 3.11 is the active interpreter.
- `toll/` already contains `tasks/`, `executions/`, `shared_memory/`, `reputation/`, `runtime/`, `operations/`, `operations/routers`-style patterns under `api/routers/`.
- Tests: `pytest` (with `.venv/bin/python`).
- Feature flags default to `False`; we will not auto-enable anything.
- The `ARCHITECTURE.md` is stale (pre-8B structure).
- The highest-impact remaining gaps are: siloed memory, no automation layer, missing E2E tests, and stale docs.

---

## Proposed approach

1. **Unified Memory Gateway** — one `toll/memory/gateway.py` wrapping `MemoryGraph`, `SharedMemory`, `ReputationService`, `ExecutionRepository`, and `RuntimeMemory`. Services stop calling 4 different imports and only import the gateway.
2. **Async Task Dispatcher** — add a thin background queue using `toll/tasks/service.py` + `toll/executions/service.py` to run long jobs without blocking FastAPI handlers.
3. **Benchmark auto-quality flag cleanup** — keep default `False`, remove the stale benchmark-flag TODO comments, add a provider-cost weight option in `ProviderSelector._quality_score()`.
4. **Caching primitive** — `toll/core/cache.py` with SQLite-backed prompt-to-artifact cache gated by `artifact_cache` flag.
5. **Adapter debt sweep** — remove or document stub adapters in `toll/adapters/`.
6. **E2E integration scaffold** — one lifecycle test under `tests/executions/` proving Chat -> Planner -> PIE -> Service -> Adapter -> Artifact.
7. **ARCHITECTURE.md update** — reflect Layers 1-3 using actual current paths.

---

## Step-by-step plan

### Task 1: Add failing integration test scaffold

**Files:**
- Create: `tests/executions/test_e2e_lifecycle.py`

**Step 1: Write failing test**

```python
def test_full_lifecycle_creates_artifact(client, db):
    from toll.application.chat_service import ChatService
    from toll.planner.planner import Planner
    from toll.prompt.engine import PromptIntelligenceEngine

    chat = ChatService()
    planner = Planner()
    engine = PromptIntelligenceEngine()

    result = chat.handle("ارسم منتج قهوة", user_id="u1")
    plan = planner.plan(result.message)

    package = engine.resolve(result.message, media_type="image", execution_profile="product_ad")
    media = MediaService().generate(package, plan.steps[0].output_type)

    assert media.artifact_id is not None
```

**Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/executions/test_e2e_lifecycle.py -v`
Expected: FAIL (missing mocks / provider not configured)

**Step 3: Add minimal mocks and fixtures**

Update `tests/conftest.py` with `fake_media_adapter` that returns a deterministic `artifact_id`.

**Step 4: Re-run**

Expected: PASS or SKIP based on feature flags.

**Step 5: Commit**

```bash
git add tests/executions/test_e2e_lifecycle.py tests/conftest.py
git commit -m "test: add e2e lifecycle scaffold"
```

---

### Task 2: Add lightweight SQLite-backed cache

**Files:**
- Create: `toll/core/cache.py`
- Modify: `toll/application/media_service.py`, `toll/application/research_service.py`, `toll/application/report_service.py`, `toll/application/presentation_service.py`
- Test: `tests/core/test_cache.py`

**Step 1: Write failing test**

```python
def test_cache_roundtrip(redis_client):
    from toll.core.cache import CacheService
    cache = CacheService()
    cache.set("k1", {"a": 1})
    assert cache.get("k1") == {"a": 1}
    assert cache.get("missing") is None
```

**Step 2: Run**

Expected: FAIL (module does not exist)

**Step 3: Minimal implementation**

```python
class CacheService:
    def __init__(self, conn):
        self.conn = conn
        self.conn.execute("CREATE TABLE IF NOT EXISTS cache (k TEXT PRIMARY KEY, v TEXT, ttl INTEGER)")
    def set(self, k, v, ttl=None):
        self.conn.execute("INSERT OR REPLACE INTO cache (k,v,ttl) VALUES (?,?,?)", (k, json.dumps(v), ttl))
    def get(self, k):
        row = self.conn.execute("SELECT v FROM cache WHERE k=?", (k,)).fetchone()
        return json.loads(row["v"]) if row else None
```

**Step 4: Write failing test for hit**

Run: `pytest tests/core/test_cache.py -v`
Expected: PASS

**Step 5: Wire `artifact_cache` flag into services**

In each service, after PIE resolves:
```python
if feature_flags.is_enabled("artifact_cache"):
    cached = cache.get(cache_key)
    if cached:
        return Artifact(**cached)
```

**Step 6: Commit**

```bash
git add toll/core/cache.py tests/core/test_cache.py
git commit -m "feat: add feature-flagged artifact cache"
```

---

### Task 3: Introduce MemoryGateway

**Files:**
- Create: `toll/memory/gateway.py`
- Modify: `toll/application/*_service.py`, `toll/planner/planner.py`, `toll/context/engine.py`
- Test: `tests/memory/test_gateway.py`

**Step 1: Write failing test**

```python
def test_gateway_unified_read(client):
    from toll.memory.gateway import MemoryGateway
    g = MemoryGateway(client)
    g.remember("global", "key1", "value1")
    g.remember("workspace", "ws1", "value2")
    assert g.recall("key1") == "value1"
    assert g.recall("ws1") == "value2"
```

**Step 2: Run**

Expected: FAIL

**Step 3: Minimal gateway implementation**

```python
class MemoryGateway:
    def __init__(self, graph, shared, reputation, executions, runtime):
        self.graph = graph
        self.shared = shared
        self.reputation = reputation
        self.executions = executions
        self.runtime = runtime

    def remember(self, scope, key, value):
        ...
    def recall(self, key, scope=None):
        ...
    def link(self, source, target, relation):
        ...
```

**Step 4: Update call sites**

Replace direct `from toll.memory.graph import MemoryGraph` and `from toll.shared_memory.service import SharedMemoryService` in application services with `gateway = MemoryGateway(...)` injection via `HandlerRegistry`.

**Step 5: Run existing tests**

Run: `.venv/bin/python -m pytest tests/memory tests/application -q`
Expected: same pass count as before

**Step 6: Commit**

```bash
git add toll/memory/gateway.py tests/memory/test_gateway.py
git commit -m "refactor: add Unified MemoryGateway"
```

---

### Task 4: Async Task Dispatcher (background queue)

**Files:**
- Create: `toll/tasks/dispatcher.py`
- Modify: `toll/tasks/service.py`, `api/routers/tasks.py` (if present), `api/main.py`
- Test: `tests/tasks/test_dispatcher.py`

**Step 1: Write failing test**

```python
def test_dispatcher_runs_in_background(event_loop):
    from toll.tasks.dispatcher import TaskDispatcher
    d = TaskDispatcher()
    task = d.submit(lambda x: x + 1, 41)
    result = d.wait(task.id, timeout=2)
    assert result == 42
```

**Step 2: Run**

Expected: FAIL

**Step 3: Minimal implementation**

```python
class TaskDispatcher:
    def __init__(self):
        self._queue = asyncio.Queue()
        self._workers = []

    async def start(self):
        for _ in range(2):
            self._workers.append(asyncio.create_task(self._worker()))

    async def submit(self, fn, *args, **kwargs):
        fut = asyncio.Future()
        await self._queue.put((fn, args, kwargs, fut))
        return fut
```

**Step 4: Wire into lifespan**

In `api/main.py`, call `await dispatcher.start()` and `await dispatcher.stop()` during startup/shutdown.

**Step 5: Run tests**

```bash
.venv/bin/python -m pytest tests/tasks/test_dispatcher.py tests/tasks -q
```

Expected: PASS

**Step 6: Commit**

```bash
git add toll/tasks/dispatcher.py tests/tasks/test_dispatcher.py api/main.py
git commit -m "feat: add async task dispatcher"
```

---

### Task 5: Benchmark flag cleanup + cost weight

**Files:**
- Modify: `toll/core/provider_selector.py`, `toll/benchmark/service.py`
- Test: `tests/benchmark/test_provider_selection.py`

**Step 1: Write failing test**

```python
def test_selector_prefers_lower_cost_when_tied(fake_registry):
    from toll.core.provider_selector import ProviderSelector
    ps = ProviderSelector(registry=fake_registry)
    model = ps.select(profile="research")
    assert model.provider_id == "cheap"
```

**Step 2: Run**

Expected: FAIL or existing selection behavior

**Step 3: Update `_quality_score()`**

Add optional `cost_weight` param; keep `benchmark_auto_quality` default `False`.

**Step 4: Run tests**

Expected: PASS with mocked data

**Step 5: Commit**

```bash
git add toll/core/provider_selector.py toll/benchmark/service.py tests/benchmark/test_provider_selection.py
git commit -m "feat: benchmark cost-aware selection (flag-gated)"
```

---

### Task 6: Stub adapter debt sweep

**Files:**
- Modify: `toll/adapters/media/*.py`, `toll/adapters/research/*.py`, docs

**Step 1: Audit adapters**

```bash
grep -R "NotImplementedError" toll/adapters
```

**Step 2: For each stub**

- If used in production: implement or raise with clear docstring.
- If unused: remove and add a DEBT note in `docs/KNOWN_GAPS.md`.

**Step 3: Run tests**

```bash
.venv/bin/python -m pytest tests/adapters -q
```

**Step 4: Commit**

```bash
git add toll/adapters docs/KNOWN_GAPS.md
git commit -m "chore: sweep stub adapter debt"
```

---

### Task 7: Update ARCHITECTURE.md

**Files:**
- Modify: `ARCHITECTURE.md`

**Step 1: Update Layer 1 to current reality**

```markdown
### Core Layer (current)
toll/core/ — flags, settings, registry, connection_manager, cache
toll/memory/ — graph + gateway
toll/planner/ — intent classification
toll/context/ — workspace-aware retrieval
toll/prompt/ — PIE + profiles + memory
toll/tasks/ + toll/executions/ — async dispatch
toll/operations/ — usage, cost, storage, cleanup, dashboard
```

**Step 2: Update Layer 2 / Layer 3**

Map `KNOWN_GAPS.md` items into Layer 2 (disabled by default) and Layer 3 (future).

**Step 3: Update Request Lifecycle diagram**

Include `MemoryGateway` and `TaskDispatcher`.

**Step 4: Commit**

```bash
git add ARCHITECTURE.md
git commit -m "docs: refresh architecture for Sprint 9"
```

---

## Tests / validation

- Run the full suite after every task: `.venv/bin/python -m pytest -q`
- Expected baseline: ~455 passed (8B baseline 453 + up to 2 new tests per task before wiring)
- Final target: ≥ 470 passed with 0 skipped new tests
- Validate with: `.venv/bin/python -m pytest tests/executions tests/tasks tests/memory tests/core -q`

---

## Files likely to change

- `toll/memory/gateway.py` (new)
- `toll/core/cache.py` (new)
- `toll/tasks/dispatcher.py` (new)
- `toll/application/media_service.py`
- `toll/application/research_service.py`
- `toll/application/report_service.py`
- `toll/application/presentation_service.py`
- `toll/planner/planner.py`
- `toll/context/engine.py`
- `toll/core/provider_selector.py`
- `toll/benchmark/service.py`
- `api/main.py`
- `ARCHITECTURE.md`
- `docs/KNOWN_GAPS.md`
- `tests/**`

---

## Risks, tradeoffs, and open questions

- **Risk:** MemoryGateway becomes a god object if we leak domain-specific methods. *Mitigation:* keep it to CRUD + link + query interfaces only.
- **Risk:** Async dispatcher adds complexity to SQLite WAL concurrency. *Mitigation:* run dispatcher in-process with a bounded queue and single-writer acquisition.
- **Tradeoff:** We are not enabling `benchmark_auto_quality` by default; it remains opt-in to preserve backward cost behavior.
- **Open question:** Should video generation adapters be tackled in Sprint 9 or kept in Layer 3? Recommend Layer 3 until the dispatcher + caching are stable.
