# Sprint 8 — Operations Layer — Design Review

> **Status**: Design Review  
> **Tag After**: v0.7c-prompt-learning-loop  
> **Do NOT implement** — design only.

---

## 1. Usage Center

### Purpose

Track every generation request through the system — per provider, per model, per resource type. Enable cost estimation, quota enforcement, and historical analysis.

### Data Model

New table `usage_log`:

```sql
CREATE TABLE usage_log (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    model_id TEXT,
    media_type TEXT NOT NULL DEFAULT 'text',
    resource_type TEXT NOT NULL DEFAULT 'request',
    resource_count INTEGER NOT NULL DEFAULT 1,
    estimated_cost_cents REAL,
    prompt_tokens INTEGER,
    generated_tokens INTEGER,
    duration_ms INTEGER,
    success INTEGER NOT NULL DEFAULT 1,
    error TEXT,
    artifact_id TEXT,
    profile_id TEXT,
    execution_profile_id TEXT,
    workspace_type TEXT,
    workspace_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_usage_created ON usage_log(created_at);
CREATE INDEX idx_usage_provider ON usage_log(provider);
CREATE INDEX idx_usage_model ON usage_log(model_id);
CREATE INDEX idx_usage_type ON usage_log(media_type);
```

New table `usage_aggregates`:

```sql
CREATE TABLE usage_aggregates (
    id TEXT PRIMARY KEY,
    period TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    provider TEXT,
    model_id TEXT,
    media_type TEXT,
    request_count INTEGER NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    total_duration_ms INTEGER NOT NULL DEFAULT 0,
    total_cost_cents REAL NOT NULL DEFAULT 0.0,
    UNIQUE(period, period_start, provider, model_id, media_type)
);
```

### UsageService

Reuses `cost_per_unit` and `cost_unit` from the Model Registry's `models` table.

```python
class UsageService:
    def record(self, provider, model_id, media_type, success=True,
               duration_ms=0, error=None, artifact_id=None,
               profile_id=None, ...):
        """Insert a row into usage_log."""

    def daily_cost(self, days=30) -> list[dict]:
        """Return daily cost breakdown."""

    def cost_by_provider(self, period="month") -> list[dict]:
        """Aggregate cost per provider."""

    def cost_by_model(self, period="month") -> list[dict]:
        """Aggregate cost per model."""

    def error_rate(self, provider=None, hours=24) -> float:
        """Return error rate for last N hours."""

    def avg_latency(self, provider=None, hours=24) -> float:
        """Return average latency for last N hours."""
```

### Cost Calculation

Each model in the Model Registry has `cost_per_unit` and `cost_unit` (e.g., `0.002` per `"image"`). The `UsageService` calculates `estimated_cost_cents` at record time:

```python
model = model_registry.get(model_id)
if model and model.cost_per_unit:
    units = resource_count  # 1 request = 1 unit typically
    cost_cents = model.cost_per_unit * units * 100
```

### Wire Points

- `MediaService.generate()` — call `usage_service.record()` after generation
- `ReportService.execute()` — call after AI ask
- `PresentationService.execute()` — call after AI ask
- `ResearchService.execute()` — call after synthesis
- PIE `resolve()` — call for prompt optimization usage

---

## 2. Provider Dashboard

### Purpose

Real-time visibility into provider health, performance, and available models. Consolidates data from Provider Registry, Usage Log, and Model Registry.

### Data Sources

| Field | Source |
|-------|--------|
| Provider name | `ProviderRegistry.all_llm()`, `ProviderRegistry.all_media()` |
| Available | `ProviderRegistry.status()` |
| Last successful request | `MAX(created_at) FROM usage_log WHERE success=1 AND provider=X` |
| Error rate (24h) | `COUNT(*) WHERE error IS NOT NULL / COUNT(*) WHERE created_at > now-24h` |
| Average latency (24h) | `AVG(duration_ms) FROM usage_log WHERE created_at > now-24h` |
| Available models | `ModelRegistry.list(provider=X)` |
| Total requests (24h) | `COUNT(*) FROM usage_log WHERE created_at > now-24h` |

### ProviderDashboard API (read-only)

```python
class ProviderDashboardService:
    def summary(self) -> list[dict]:
        """Return all providers with status, error rate, latency, model count."""

    def provider_detail(self, name) -> dict:
        """Return detailed metrics for one provider."""

    def model_breakdown(self, provider) -> list[dict]:
        """Per-model metrics: requests, latency, cost, error rate."""
```

### UI Wireframe

```
┌─────────────────────────────────────────────────────┐
│  Operations                                         │
│  ┌──────┬──────────┬─────────┬──────────┐           │
│  │ Usage│Providers │ Storage │ Cleanup  │           │
│  └──────┴──────────┴─────────┴──────────┘           │
│                                                      │
│  Provider Summary                                    │
│  ┌──────────┬────┬──────┬──────┬────┬──────────┐   │
│  │ Provider │Sta │ Err% │ Avg  │Req │ Models   │   │
│  │          │tus │      │ Lat  │    │          │   │
│  ├──────────┼────┼──────┼──────┼────┼──────────┤   │
│  │ opencode │ ✅ │ 2.1% │ 1.2s │ 45 │ big      │   │
│  │          │    │      │      │    │ pickle   │   │
│  ├──────────┼────┼──────┼──────┼────┼──────────┤   │
│  │ ollama   │ ⚠️ │ 15%  │ 8.5s │ 20 │ qwen2.5 │   │
│  ├──────────┼────┼──────┼──────┼────┼──────────┤   │
│  │ replicate│ ✅ │ 0%   │ 3.1s │ 12 │ flux,    │   │
│  │          │    │      │      │    │ sdxl     │   │
│  └──────────┴────┴──────┴──────┴────┴──────────┘   │
│                                                      │
│  [click row → expand detail with model breakdown]    │
└─────────────────────────────────────────────────────┘
```

---

## 3. Cost Monitoring

### Purpose

Track spending over time with daily, weekly, and monthly granularity. Break down costs by provider and model.

### Aggregation Strategy

Pre-compute aggregates in a background-friendly way: on every `usage_service.record()` call, also upsert into the appropriate daily aggregate row. Weekly and monthly aggregates are computed on read by summing daily rows.

```python
def _update_aggregate(self, usage_row):
    day = usage_row.created_at[:10]  # "2026-06-22"
    key = f"daily:{day}:{usage_row.provider}:{usage_row.model_id or ''}"
    # UPSERT into usage_aggregates
```

### CostService

```python
class CostService:
    def daily(self, days=30) -> list[dict]:
        """Daily cost breakdown, last N days."""

    def weekly(self, weeks=12) -> list[dict]:
        """Weekly cost breakdown."""

    def monthly(self, months=6) -> list[dict]:
        """Monthly cost breakdown."""

    def by_provider(self, start_date, end_date) -> list[dict]:
        """Cost per provider for date range."""

    def by_model(self, start_date, end_date) -> list[dict]:
        """Cost per model for date range."""
```

### Cost Data Display

```
  Daily Cost (Last 30 Days)
  ┌─────────────────────────────────────────────┐
  │  ██                                        │
  │  ██ ██                                     │
  │  ██ ██ ██                                  │
  │  ██ ██ ██ ██    ██                         │
  │  ██ ██ ██ ██ ██ ██ ██ ██ ██                │
  │  ────────────────────────────────────       │
  │  Jun 01                    Jun 30           │
  │                                             │
  │  Total: $12.45  │  Avg: $0.42/day           │
  └─────────────────────────────────────────────┘
```

---

## 4. Storage Management

### Purpose

Track disk usage per media type, artifact counts, published assets, pending cleanup. Drive the cleanup system.

### StorageService

Reuses `ArtifactRepository` and `FsMediaStorage` file enumeration.

```python
class StorageService:
    def usage_by_type(self) -> dict:
        """Return {media_type: {count, total_bytes, path}}."""

    def artifact_counts(self) -> dict:
        """Return {status: count} for all artifacts."""

    def published_assets(self) -> list[dict]:
        """Return artifacts with rendered_path set."""

    def pending_cleanup(self, older_than_days=4) -> list[dict]:
        """Return artifacts eligible for cleanup."""

    def retention_policies(self) -> list[dict]:
        """Return all configured policies."""

    def cleanup_dry_run(self) -> dict:
        """Preview what cleanup would delete without executing."""
```

### Retention Policies Table

```sql
CREATE TABLE retention_policies (
    id TEXT PRIMARY KEY,
    workspace_type TEXT,
    workspace_id TEXT,
    media_type TEXT,
    retention_days INTEGER NOT NULL DEFAULT 4,
    keep_metadata INTEGER NOT NULL DEFAULT 1,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

---

## 5. Cleanup System

### Purpose

Auto-delete published assets older than the retention period. Default: 4 days. Keep metadata (artifact record) but delete the rendered file. Configurable per workspace and media type.

### CleanupService

```python
class CleanupService:
    def run(self, dry_run=True) -> dict:
        """Execute cleanup for all enabled policies."""

    def run_for_policy(self, policy, dry_run=True) -> dict:
        """Execute cleanup for a single policy."""

    def simulate(self) -> dict:
        """Show what would be deleted without executing."""
```

### Cleanup Logic

1. Query all `retention_policies` where `enabled = True`
2. For each policy, find artifacts matching `workspace_type`, `workspace_id`, `media_type`, and `created_at < now - retention_days`
3. For each matched artifact:
   - If `rendered_path` exists and file is on disk: delete the file
   - If `keep_metadata`: set `rendered_path = None`, `preview_url = None`, add `metadata.cleaned_at` timestamp
   - If not `keep_metadata`: soft-delete the artifact
4. Log all actions to a `cleanup_log` table

### Cleanup Trigger

- Called via a new `POST /api/operations/cleanup` endpoint (manual trigger)
- Could be scheduled via a simple cron-like mechanism (future)
- Dry-run mode for preview: `POST /api/operations/cleanup?dry_run=true`

### Cleanup Log Table

```sql
CREATE TABLE cleanup_log (
    id TEXT PRIMARY KEY,
    policy_id TEXT REFERENCES retention_policies(id),
    artifact_id TEXT,
    action TEXT NOT NULL,
    file_size_bytes INTEGER,
    details TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

---

## 6. Caching Layer

### Purpose

Avoid redundant computation by caching deterministic results. Four distinct caches with different TTLs.

### Cache Table

```sql
CREATE TABLE cache_entries (
    cache_key TEXT PRIMARY KEY,
    cache_type TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT
);

CREATE INDEX idx_cache_type ON cache_entries(cache_type);
```

### Cache Types

| Cache Type | TTL | Key | Value | Purpose |
|---|---|---|---|---|
| `context` | 5 min | `context:{message_hash}` | JSON serialized `ContextResult` | Avoid rebuilding context for identical messages |
| `prompt` | 1 hour | `prompt:{profile}:{model}:{input_hash}` | JSON `PromptPackage` | Cache optimized prompt output for repeated inputs |
| `benchmark` | 1 hour | `benchmark:avg:{model_id}` | JSON scores dict | Cache `avg_scores()` results |
| `research` | 30 min | `research:search:{query_hash}` | JSON search results | Cache DuckDuckGo research results |

### CacheService

```python
class CacheService:
    def get(self, cache_key: str, cache_type: str) -> str | None: ...

    def set(self, cache_key: str, cache_type: str, value: str,
            ttl_seconds: int = 300): ...

    def invalidate(self, cache_type: str | None = None,
                   cache_key: str | None = None): ...

    def clear_expired(self) -> int:
        """Delete all expired entries. Returns count."""
```

### Wire Points

| Cache Type | Where to Add | Benefit |
|---|---|---|
| `context` | Before `ContextEngine.build()` | Avoid redundant context building for identical messages within 5 min |
| `prompt` | Before `PIE.resolve()` | Cache prompt output for identical inputs + profile + model |
| `benchmark` | Before `BenchmarkRepository.avg_scores()` | Avoid repeated AVG queries |
| `research` | Before `SourceManager.collect()` | Avoid repeated web searches for same query |

---

## 7. Operations UI

### Navigation

Add a new entry in the ZUNO sidebar navigation (between "Lab" and "Settings"):

```
Chat
Notebooks
Models
Lab
⚙ Operations     ← NEW
Settings
```

### Operations Panel Layout

```
┌─────────────────────────────────────────────────────┐
│ ⚙ Operations                              [close]  │
│                                                      │
│ ┌──────┬──────────┬─────────┬──────────┐            │
│ │ Usage│Providers │ Storage │ Cleanup  │            │
│ └──────┴──────────┴─────────┴──────────┘            │
│                                                      │
│ [Tab content rendered below]                         │
└─────────────────────────────────────────────────────┘
```

### Tab: Usage

```
┌─────────────────────────────────────────────────────┐
│ 📊 Usage Overview                                    │
│                                                      │
│ Today        This Week      This Month               │
│ $0.42        $2.89          $12.45                   │
│ 18 requests  142 requests   612 requests             │
│                                                      │
│ ┌──────────── Daily Cost ────────────────────────┐   │
│ │  [Chart.js mini line chart, 30 days]           │   │
│ └────────────────────────────────────────────────┘   │
│                                                      │
│ Cost by Provider                                     │
│ opencode  $6.20  ████████████░░░░░░  52%             │
│ ollama    $3.45  ███████░░░░░░░░░░░  29%             │
│ replicate $2.80  █████░░░░░░░░░░░░░  23%             │
└─────────────────────────────────────────────────────┘
```

### Tab: Providers

```
┌─────────────────────────────────────────────────────┐
│ 🔌 Provider Status                                   │
│                                                      │
│ ┌─────────┬──────┬──────┬──────┬──────┬──────────┐  │
│ │Provider │Status│ Err% │ Lat  │ Reqs │ Models   │  │
│ ├─────────┼──────┼──────┼──────┼──────┼──────────┤  │
│ │opencode │ ✅   │ 2.1% │ 1.2s │  45  │ big      │  │
│ │         │      │      │      │      │ pickle   │  │
│ ├─────────┼──────┼──────┼──────┼──────┼──────────┤  │
│ │ollama   │ ⚠️   │ 15%  │ 8.5s │  20  │ qwen2.5  │  │
│ ├─────────┼──────┼──────┼──────┼──────┼──────────┤  │
│ │replicate│ ✅   │  0%  │ 3.1s │  12  │ flux,    │  │
│ │         │      │      │      │      │ sdxl     │  │
│ └─────────┴──────┴──────┴──────┴──────┴──────────┘  │
└─────────────────────────────────────────────────────┘
```

### Tab: Storage

```
┌─────────────────────────────────────────────────────┐
│ 💾 Storage Usage                                     │
│                                                      │
│ Total: 245 MB across 1,892 artifacts                 │
│                                                      │
│ ┌──────────┬──────────┬──────────┬────────────────┐  │
│ │ Type     │ Count    │ Size     │ Location       │  │
│ ├──────────┼──────────┼──────────┼────────────────┤  │
│ │ Reports  │      142 │  12 MB   │ data/artifacts │  │
│ │ Images   │    1,200 │ 210 MB   │ data/media     │  │
│ │ Carousels│      350 │  15 MB   │ data/artifacts │  │
│ │ Research │      200 │   8 MB   │ data/artifacts │  │
│ └──────────┴──────────┴──────────┴────────────────┘  │
│                                                      │
│ Retention Policies (4d default)                      │
│ ┌──────────┬──────┬──────────┬────────┐             │
│ │ Type     │ Days │ Keep Meta│Enabled │             │
│ ├──────────┼──────┼──────────┼────────┤             │
│ │ Default  │    4 │ ✅       │ ✅     │             │
│ │ Images   │    7 │ ✅       │ ✅     │             │
│ │ Research │   30 │ ✅       │ ❌     │             │
│ └──────────┴──────┴──────────┴────────┘             │
└─────────────────────────────────────────────────────┘
```

### Tab: Cleanup

```
┌─────────────────────────────────────────────────────┐
│ 🗑 Cleanup                                            │
│                                                      │
│ Pending cleanup: 1,450 artifacts (210 MB)            │
│                                                      │
│ [Run Dry Run]  [Execute Cleanup]                     │
│                                                      │
│ ┌──────────┬──────────┬──────────┬────────────────┐  │
│ │ Policy   │ Aged     │ Files    │ Size           │  │
│ ├──────────┼──────────┼──────────┼────────────────┤  │
│ │ Default  │ 4d+      │ 1,200    │ 198 MB         │  │
│ │ Images   │ 7d+      │   250    │  12 MB         │  │
│ └──────────┴──────────┴──────────┴────────────────┘  │
│                                                      │
│ [Cleanup Log — Last 10 Actions]                      │
│ 2026-06-22  Deleted  media/img_123.png  (210 KB)     │
│ 2026-06-22  Kept    report_456 (metadata only)       │
│ ...                                                  │
└─────────────────────────────────────────────────────┘
```

---

## 8. API Changes

### New Endpoints

All under `/api/operations` prefix:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/operations/usage/summary` | Usage counts + cost for today/week/month |
| `GET` | `/api/operations/usage/daily?days=30` | Daily usage + cost breakdown |
| `GET` | `/api/operations/usage/by-provider` | Usage grouped by provider |
| `GET` | `/api/operations/usage/by-model` | Usage grouped by model |
| `GET` | `/api/operations/providers` | All providers with status, error rate, latency |
| `GET` | `/api/operations/providers/{name}` | Detailed provider metrics |
| `GET` | `/api/operations/storage` | Storage usage by type |
| `GET` | `/api/operations/storage/retention` | List retention policies |
| `POST` | `/api/operations/storage/retention` | Create/update retention policy |
| `DELETE` | `/api/operations/storage/retention/{id}` | Delete retention policy |
| `POST` | `/api/operations/cleanup?dry_run=true` | Run cleanup (dry run or execute) |
| `GET` | `/api/operations/cleanup/log` | Cleanup action history |
| `GET` | `/api/operations/cache/stats` | Cache hit rates and size |
| `POST` | `/api/operations/cache/clear` | Invalidate all/type-specific cache |

### Wire Points in Existing Services

| Service | Hook | Records |
|---------|------|---------|
| `MediaService.generate()` | After adapter result | `usage_log` + cost |
| `ReportService.execute()` | After `ai.ask()` | `usage_log` + cost |
| `PresentationService.execute()` | After `ai.ask()` | `usage_log` + cost |
| `ResearchService.execute()` | After `_synthesize()` | `usage_log` + cost |
| `PIE.resolve()` | Before/after context + prompt | context cache, prompt cache |
| `BenchmarkRepository.avg_scores()` | Before query | benchmark cache |
| `SourceManager.collect()` | Before web search | research cache |

---

## 9. Database Changes

### New Tables (4)

| Table | Columns | Indexes | Purpose |
|-------|---------|---------|---------|
| `usage_log` | 17 columns | 4 | Granular usage records |
| `usage_aggregates` | 12 columns | 1 unique | Pre-computed daily aggregates |
| `cache_entries` | 5 columns | 1 | Generic KV cache with TTL |
| `retention_policies` | 8 columns | 0 | Configurable cleanup policies |
| `cleanup_log` | 6 columns | 0 | Cleanup action audit trail |

### Migration

`0013_operations_layer.sql` — 5 tables, 6 indexes.

---

## 10. Test Plan

| Test Group | Count | What It Tests |
|---|---|---|
| `UsageService` | 10 | Record, daily cost, by-provider, by-model, error rate, avg latency |
| `CostService` | 6 | Daily/weekly/monthly aggregation, cost calc |
| `StorageService` | 8 | Usage by type, artifact counts, pending cleanup, retention CRUD |
| `CleanupService` | 6 | Dry run, execute, keep metadata, policy filtering |
| `CacheService` | 8 | Get/set, TTL, invalidation, clear expired |
| `Operations API` | 12 | All 13 endpoints, dry run, error cases |
| **Total** | **~50** | |

---

## 11. Estimated Effort

| Module | Files | Tests | Effort |
|--------|-------|-------|--------|
| UsageService + UsageRepository | 4 | 10 | 2 days |
| CostService + aggregation | 2 | 6 | 1.5 days |
| StorageService + retention | 3 | 8 | 2 days |
| CleanupService + cleanup log | 3 | 6 | 1.5 days |
| CacheService | 2 | 8 | 1 day |
| API router (`operations.py`) | 1 | 12 | 1.5 days |
| UI (Operations panel + 4 tabs) | 1 | — | 2 days |
| Migration 0013 | 1 | — | 0.5 day |
| Wire usage hooks into services | 4 | — | 0.5 day |
| **Total** | **~21** | **~50** | **~12 days** |

---

## 12. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Usage recording adds latency to generation path | Medium | Async recording via background thread; batch inserts |
| Cost calculation is approximate (model `cost_per_unit` may be stale) | Low | Add `last_updated` to model; flag stale costs in UI |
| Cleanup accidentally deletes user data | High | Dry-run mode always default; explicit confirmation required; trash/undo window |
| Cache invalidation is manual | Medium | Add TTL-based auto-expiry; manual clear button in UI for emergencies |
| Aggregation queries on large `usage_log` table are slow | Low | Pre-computed daily aggregates; index on `created_at`; partition by month |
| No scheduled cleanup (cron/scheduler not implemented) | Medium | Manual trigger via API; document that cleanup is currently manual |

---

## 13. Sprint 8 Sprint Breakdown

### Sprint 8A — Core Infrastructure (5-6 days)

**Backend** — services, repository, migration, usage hooks

- `toll/operations/usage_service.py` — `UsageService` + `UsageRepository`
- `toll/operations/cost_service.py` — `CostService`
- `toll/operations/storage_service.py` — `StorageService`
- `toll/operations/cleanup_service.py` — `CleanupService`
- `toll/operations/cache_service.py` — `CacheService`
- `toll/model/migrations/0013_operations_layer.sql`
- `api/routers/operations.py` — all 13 endpoints
- Wire usage hooks into `MediaService`, `ReportService`, `PresentationService`, `ResearchService`, `PIE`, `BenchmarkRepository`, `SourceManager`
- Feature flags: `operations_layer` (default True), `cache_enabled` (default True), `cleanup_auto` (default False)
- ~50 tests
- **Deliverables**: All services functional, API operational, usage tracking live

### Sprint 8B — Operations UI (2-3 days)

**Frontend** — panel, tabs, charts

- Operations nav item in sidebar
- Usage tab with Chart.js daily cost chart
- Providers tab with status table
- Storage tab with type breakdown + retention policy editor
- Cleanup tab with dry-run preview + execute button + log viewer
- **Deliverables**: Full Operations panel functional in ZUNO UI

### Total Sprint 8: ~8-9 days engineering, ~21 files, ~50 tests
