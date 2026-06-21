# Sprint 6A — Model Registry & Benchmark Lab

**Status:** Design  
**Target:** v0.7.0-model-registry  
**Depends on:** Sprint 5C (Research Memory)  

---

## 1. Motivation

The current provider system (`ProviderRegistry` in `toll/core/registry.py`) hardcodes two LLM providers (opencode, ollama) and one search provider (duckduckgo) at import time. The Sprint 6 Media Layer design repeats this pattern — each adapter carries a `MODELS` dict hardcoded in Python code. This approach breaks under the requirements:

**Problems with hardcoded models:**
- Adding a new model requires editing Python source and redeploying
- The selector (`ProviderSelector._quality_score`) is a hardcoded dict — new providers require code changes
- No way to track model versions, deprecations, or capabilities over time
- No data to answer "which model is fastest for this task?" or "which is cheapest?"
- Users cannot see what models are available or compare them

**Model Registry solves:**
- Dynamic registration — models live in SQLite, added via API or seed data
- Provider-agnostic — any provider can register any number of models
- Capability-aware — each model declares what it can do (image, audio, video, LLM, search)
- Versioned — track model versions, deprecation, sunset dates

**Benchmark Lab solves:**
- Systematic quality/speed/cost measurement across models
- Data-driven model selection instead of hardcoded quality scores
- Reproducible benchmark suites for regression testing
- User-visible comparison UI

---

## 2. Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Application Layer                      │
│  ModelRegistryService  │  BenchmarkService                  │
├──────────────────────────────────────────────────────────┤
│                    Ports (Abstract)                        │
│  ModelRegistryPort  │  BenchmarkPort                        │
├──────────────────────────────────────────────────────────┤
│                     Storage Layer                          │
│  models (SQLite)  │  benchmark_runs (SQLite)               │
│                   │  benchmark_outputs (FS: data/bench/)   │
├──────────────────────────────────────────────────────────┤
│                     Integration Layer                      │
│  MediaService  │  ProviderSelector  │  AI  │  Adapters     │
└──────────────────────────────────────────────────────────┘
```

### 2.1 How It Integrates with Sprint 6

The Sprint 6 Media Layer design currently has hardcoded `MODELS` dicts in each adapter. The Model Registry replaces this:

**Before (Sprint 6 design):**
```
ReplicateMediaAdapter.MODELS = {"image": {"flux-schnell": "..."}}
MediaService → hardcoded adapter.MODELS lookup
```

**After (with Model Registry):**
```
models table:  row(provider="replicate", provider_model_id="...", name="Flux Schnell")
MediaService → ModelRegistry.lookup("flux-schnell") → {provider, provider_model_id, params}
MediaService → adapter.generate(request, provider_model_id)
```

The adapter no longer owns model definitions. It owns only the connection/authentication and the `generate()` call. The registry owns model metadata.

### 2.2 Design Constraints

- **Local-first** — registry is SQLite, no external dependencies
- **Data-driven** — all model metadata in rows, not in code
- **Provider adapter is stateless** — adapter receives `MediaRequest` with fully resolved `provider_model_id`
- **Read-heavy** — registry is queried on every generation (cache-friendly)
- **Write-light** — models are registered on setup or admin action, not per-request
- **Benchmark outputs are files** — generated images/audio/video from benchmarks stored in `data/bench/`

---

## 3. Database Schema (Migration 0011)

```sql
-- Migration: 0011_model_registry.sql

-- Core model registry
CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,                                  -- "replicate:flux-schnell"
    provider TEXT NOT NULL,                                -- "replicate" | "openai" | "fal" | "veo" | "runway"
    provider_model_id TEXT NOT NULL,                       -- "black-forest-labs/flux-schnell"
    name TEXT NOT NULL,                                    -- "Flux Schnell"
    description TEXT DEFAULT '',
    version TEXT,                                          -- "1.0.0" or commit hash
    family TEXT,                                           -- "flux", "sdxl", "dall-e", "gpt", "claude"
    media_types TEXT NOT NULL DEFAULT '["image"]',         -- JSON array: ["image"], ["audio","video"], ["llm"]
    capabilities TEXT NOT NULL DEFAULT '{}',               -- JSON: {"max_width": 1024, "max_height": 1024, "supports_negative_prompt": true}
    default_params TEXT NOT NULL DEFAULT '{}',             -- JSON: {"width": 1024, "height": 1024}
    status TEXT NOT NULL DEFAULT 'active',                 -- "active" | "deprecated" | "disabled" | "coming_soon"
    cost_per_unit REAL,                                    -- e.g. 0.002 (in provider's currency unit)
    cost_unit TEXT,                                        -- "per_image" | "per_second" | "per_token" | "per_call"
    metadata TEXT DEFAULT '{}',                            -- JSON: author, training_date, license, homepage
    registered_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(provider, provider_model_id)
);

CREATE INDEX idx_models_provider ON models(provider);
CREATE INDEX idx_models_status ON models(status);
CREATE INDEX idx_models_family ON models(family);

-- Model tags for filtering/organizing
CREATE TABLE IF NOT EXISTS model_tags (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(model_id, tag)
);

CREATE INDEX idx_model_tags_tag ON model_tags(tag);

-- Benchmark suites (named collections of prompts)
CREATE TABLE IF NOT EXISTS benchmark_suites (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    prompts TEXT NOT NULL,                                  -- JSON array of prompt strings
    media_type TEXT NOT NULL,                               -- "image" | "audio" | "video" | "llm"
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Individual benchmark runs
CREATE TABLE IF NOT EXISTS benchmark_runs (
    id TEXT PRIMARY KEY,
    suite_id TEXT REFERENCES benchmark_suites(id),
    model_id TEXT NOT NULL REFERENCES models(id),
    prompt TEXT NOT NULL,
    prompt_index INTEGER,                                   -- index within suite prompts array
    media_type TEXT NOT NULL,
    provider_latency_ms INTEGER,                            -- time provider took to respond
    total_duration_ms INTEGER,                              -- wall clock including download
    file_size_bytes INTEGER,
    quality_score_auto REAL,                                -- 0-10, AI-rated
    quality_score_human REAL,                               -- 0-10, human-rated (nullable)
    cost_cents REAL,                                        -- calculated from model.cost_per_unit
    seed INTEGER,
    output_storage_key TEXT,                                -- relative path in data/bench/
    content_type TEXT,                                      -- mime type
    width INTEGER,
    height INTEGER,
    duration_ms INTEGER,                                    -- for audio/video
    error TEXT,
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_benchmark_runs_model ON benchmark_runs(model_id);
CREATE INDEX idx_benchmark_runs_suite ON benchmark_runs(suite_id);
CREATE INDEX idx_benchmark_runs_media ON benchmark_runs(media_type);
```

### 3.1 Schema Rationale

| Design Decision | Why |
|----------------|-----|
| `models.id` uses `{provider}:{slug}` format | Human-readable PK, enables direct lookup without separate auto-increment |
| `capabilities` as JSON | Future-proof — each provider exposes different parameters; rigid columns would need constant migration |
| `media_types` as JSON array | A model may support multiple types (e.g., Veo might do image + video) |
| Separate `model_tags` table | Enables efficient tag-based filtering (e.g., "all models tagged 'fast' or 'premium'") |
| `quality_score_auto` + `quality_score_human` | Supports both automated AI-rating and manual human evaluation |
| `prompt_index` in benchmark_runs | Links result back to its position in the suite for comparison displays |
| `benchmark_outputs` stored in `data/bench/` | Separate from user-generated media (`data/media/`); clear ownership boundary |

---

## 4. API Endpoints

### 4.1 Model Registry Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/models` | List models (filterable: `provider`, `media_type`, `status`, `family`, `tag`) |
| `GET` | `/api/models/{id}` | Get model details with capabilities parsed |
| `POST` | `/api/models/register` | Register a new model |
| `PUT` | `/api/models/{id}` | Update model metadata |
| `DELETE` | `/api/models/{id}` | Soft-delete (set `status=disabled`) |
| `GET` | `/api/models/providers` | List distinct providers with model counts |
| `GET` | `/api/models/query` | Find models by capability (e.g., `?media_type=image&min_width=1024`) |

**POST /api/models/register:**
```json
{
    "provider": "replicate",
    "provider_model_id": "black-forest-labs/flux-schnell",
    "name": "Flux Schnell",
    "version": "1.0.0",
    "family": "flux",
    "media_types": ["image"],
    "capabilities": {
        "max_width": 1024,
        "max_height": 1024,
        "supports_negative_prompt": true,
        "supports_seed": true
    },
    "default_params": {
        "width": 1024,
        "height": 1024,
        "num_outputs": 1
    },
    "cost_per_unit": 0.002,
    "cost_unit": "per_image",
    "tags": ["fast", "general"]
}
```

**GET /api/models?provider=replicate&media_type=image&status=active:**
```json
{
    "models": [
        {
            "id": "replicate:flux-schnell",
            "provider": "replicate",
            "name": "Flux Schnell",
            "family": "flux",
            "media_types": ["image"],
            "status": "active",
            "cost_per_unit": 0.002,
            "cost_unit": "per_image",
            "tags": ["fast", "general"]
        }
    ],
    "total": 1
}
```

### 4.2 Benchmark Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/benchmarks/runs` | List benchmark runs (filterable: `model_id`, `suite_id`, `media_type`) |
| `GET` | `/api/benchmarks/runs/{id}` | Get single run detail with output URL |
| `POST` | `/api/benchmarks/run` | Run a one-off benchmark (prompt + model_id) |
| `GET` | `/api/benchmarks/suites` | List benchmark suites |
| `POST` | `/api/benchmarks/suites` | Create a benchmark suite |
| `GET` | `/api/benchmarks/suites/{id}` | Get suite with aggregated results |
| `POST` | `/api/benchmarks/suites/{id}/run` | Execute all prompts in suite across specified models |
| `GET` | `/api/benchmarks/compare` | Compare models side-by-side |
| `GET` | `/api/benchmarks/leaderboard` | Leaderboard ranked by quality/speed/cost composite |

**POST /api/benchmarks/run:**
```json
{
    "model_id": "replicate:flux-schnell",
    "prompt": "A serene mountain landscape at sunset, digital art",
    "media_type": "image",
    "seed": 42
}
```
```json
{
    "run_id": "uuid",
    "model_id": "replicate:flux-schnell",
    "prompt": "A serene mountain landscape...",
    "provider_latency_ms": 2340,
    "total_duration_ms": 2890,
    "file_size_bytes": 524288,
    "quality_score_auto": 8.2,
    "cost_cents": 0.2,
    "seed": 42,
    "output_url": "/data/bench/runs/uuid/output.png",
    "width": 1024,
    "height": 1024
}
```

**GET /api/benchmarks/compare?models=replicate:flux-schnell,replicate:flux-pro&prompt_category=landscape:**
```json
{
    "models": [
        {
            "id": "replicate:flux-schnell",
            "name": "Flux Schnell",
            "runs": 12,
            "avg_latency_ms": 1230,
            "avg_quality": 7.8,
            "avg_cost_cents": 0.2
        },
        {
            "id": "replicate:flux-pro",
            "name": "Flux Pro",
            "runs": 12,
            "avg_latency_ms": 4560,
            "avg_quality": 9.1,
            "avg_cost_cents": 5.0
        }
    ],
    "prompt_category": "landscape",
    "total_runs": 24
}
```

---

## 5. Service Layer Design

### 5.1 Model Registry Service

```
toll/model_registry/
├── __init__.py
├── service.py          # ModelRegistryService
├── repository.py       # ModelRepository (SQL queries)
└── seed.py             # Seed data with known models
```

```python
class ModelRegistryService:
    def __init__(self, cm: ConnectionManager):
        self.repo = ModelRepository(cm)

    def register(self, data: dict) -> Model:
        """Register a new model. Returns created model or raises on conflict."""

    def get(self, model_id: str) -> Model | None:
        """Lookup model by ID."""

    def get_by_provider(self, provider: str, provider_model_id: str) -> Model | None:
        """Lookup by provider + provider_model_id pair."""

    def list(self, provider: str = None, media_type: str = None,
             status: str = None, family: str = None, tag: str = None) -> list[Model]:
        """List models with optional filters."""

    def update(self, model_id: str, data: dict) -> Model | None:
        """Update model metadata."""

    def disable(self, model_id: str) -> bool:
        """Soft-delete by setting status=disabled."""

    def find_best(self, media_type: str, prefer_speed: bool = False,
                  prefer_quality: bool = False, prefer_cost: bool = False) -> Model | None:
        """Query-based model selection using benchmark data.
        Returns highest-scoring active model for the given criteria.
        """

    def list_providers(self) -> list[str]:
        """Distinct provider names from all registered models."""

    def supported_types(self, provider: str) -> list[str]:
        """Union of media_types across all models for a provider."""
```

**`find_best()` selection algorithm:**
- Filters to active models supporting the requested `media_type`
- If benchmark data exists: scores each model by weighted criteria
- Default weights: quality 0.5, speed 0.3, cost 0.2 (configurable)
- If no benchmark data: falls back to simple availability

### 5.2 Benchmark Service

```
toll/benchmark/
├── __init__.py
├── service.py          # BenchmarkService
├── repository.py       # BenchmarkRepository
├── runner.py           # BenchmarkRunner (orchestrates execution)
├── quality_scorer.py   # AI-based quality evaluation
└── cost_calculator.py  # Cost estimation from model pricing
```

```python
class BenchmarkService:
    def __init__(self, cm: ConnectionManager, model_registry: ModelRegistryService,
                 media_service: MediaService):
        self.repo = BenchmarkRepository(cm)
        self.model_registry = model_registry
        self.runner = BenchmarkRunner(media_service)
        self.quality_scorer = QualityScorer()

    def run_single(self, model_id: str, prompt: str, media_type: str,
                   seed: int = None) -> BenchmarkRun:
        """Run a one-off benchmark: generate → measure → score → persist."""
        model = self.model_registry.get(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        result = self.runner.execute(model, prompt, media_type, seed)
        quality = self.quality_scorer.score(result, prompt)
        cost = CostCalculator.calculate(model, result)
        run = self.repo.create(result, quality, cost)
        return run

    def run_suite(self, suite_id: str, model_ids: list[str]) -> list[BenchmarkRun]:
        """Execute all prompts in a suite across all specified models."""

    def create_suite(self, name: str, prompts: list[str], media_type: str) -> BenchmarkSuite:
        """Create a named benchmark suite."""

    def compare(self, model_ids: list[str], prompt_category: str = None) -> ComparisonResult:
        """Aggregate benchmark data for side-by-side comparison."""

    def leaderboard(self, media_type: str, metric: str = "quality") -> list[dict]:
        """Rank models by composite score for a media type."""

    def get_run(self, run_id: str) -> BenchmarkRun | None:
        """Get single benchmark run with output path."""
```

### 5.3 Benchmark Runner

```python
class BenchmarkRunner:
    def __init__(self, media_service: MediaService):
        self.media_service = media_service

    def execute(self, model: Model, prompt: str, media_type: str,
                seed: int = None) -> RawBenchmarkResult:
        """Generate media and capture timing/size metrics."""
        start = time.monotonic()
        plan = {
            "intent": "media_generate",
            "media_type": media_type,
            "prompt": prompt,
            "model": model.id,
            "seed": seed,
        }
        # Benchmark hooks into media_service but intercepts the adapter call
        # to capture provider_latency separately from total_duration
        result = self.media_service.execute(plan)
        total_duration = (time.monotonic() - start) * 1000

        if "error" in result:
            return RawBenchmarkResult(error=result["error"], ...)

        return RawBenchmarkResult(
            success=True,
            output_path=result.get("media_url"),
            total_duration_ms=int(total_duration),
            provider_latency_ms=result.get("provider_latency_ms", 0),
            file_size_bytes=result.get("file_size_bytes", 0),
            width=result.get("width"),
            height=result.get("height"),
            seed=result.get("seed"),
            content_type=result.get("content_type"),
        )
```

### 5.4 Quality Scorer

```python
class QualityScorer:
    def __init__(self, ai: AI = None):
        self.ai = ai or AI()

    def score(self, result: RawBenchmarkResult, prompt: str) -> float:
        """Score output quality 0-10 using AI evaluation.
        For images: composition, prompt adherence, aesthetic quality.
        For audio: clarity, naturalness, prompt adherence.
        For video: motion smoothness, prompt adherence, visual quality.
        """
        if result.error:
            return 0.0
        # Use AI to evaluate output against prompt
        # For MVP: proxy quality score from available metrics
        # (file size as proxy for detail, latency as proxy for compute)
        return self._ai_quality_score(result.output_path, prompt)
```

---

## 6. Model Registry Port

```python
@dataclass
class Model:
    id: str                              # "replicate:flux-schnell"
    provider: str                        # "replicate"
    provider_model_id: str               # "black-forest-labs/flux-schnell"
    name: str                            # "Flux Schnell"
    description: str = ""
    version: str | None = None
    family: str | None = None
    media_types: list[str] = field(default_factory=lambda: ["image"])
    capabilities: dict = field(default_factory=dict)
    default_params: dict = field(default_factory=dict)
    status: str = "active"               # active | deprecated | disabled | coming_soon
    cost_per_unit: float | None = None
    cost_unit: str | None = None         # per_image | per_second | per_token | per_call
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    registered_at: str = ""
    updated_at: str = ""


@dataclass
class BenchmarkRun:
    id: str
    model_id: str
    prompt: str
    media_type: str
    provider_latency_ms: int = 0
    total_duration_ms: int = 0
    file_size_bytes: int = 0
    quality_score_auto: float = 0.0
    quality_score_human: float | None = None
    cost_cents: float = 0.0
    seed: int | None = None
    output_storage_key: str | None = None
    content_type: str = ""
    width: int | None = None
    height: int | None = None
    duration_ms: int | None = None
    error: str | None = None
    created_at: str = ""


@dataclass
class BenchmarkSuite:
    id: str
    name: str
    description: str = ""
    prompts: list[str] = field(default_factory=list)
    media_type: str = "image"
    created_at: str = ""
    updated_at: str = ""
```

---

## 7. UI Wireframe

### 7.1 Model Registry Page

```
┌─────────────────────────────────────────────────────────────┐
│  Models                                      [+ Register]   │
├─────────────────────────────────────────────────────────────┤
│  [All Providers ▼]  [Media Type ▼]  [Status ▼]  [Search...] │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ ○ replicate  │  ● active  │  Image  │  Flux Schnell    │ │
│  │   cost: $0.002/img  │  fast, general                    │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │ ○ replicate  │  ● active  │  Image  │  Flux Pro        │ │
│  │   cost: $0.050/img  │  premium, high-quality            │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │ ○ replicate  │  ● active  │  Image  │  SDXL            │ │
│  │   cost: $0.010/img  │  general, open-source             │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │ ○ openai     │  ○ coming  │  Image  │  DALL-E 3        │ │
│  │   TBD                                                     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                        Page 1 of 3  [→]      │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Model Detail Page

```
┌─────────────────────────────────────────────────────────────┐
│  Flux Schnell                        [Edit]  [Disable]      │
├─────────────────────────────────────────────────────────────┤
│  Provider:    replicate                                      │
│  Model ID:    black-forest-labs/flux-schnell                 │
│  Family:      flux                                           │
│  Status:      ● active                                       │
│  Media Types: Image                                          │
│  Cost:        $0.002 / per_image                             │
│                                                             │
│  Capabilities:                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ ✓ Max Resolution: 1024x1024    ✓ Seed Support           │ │
│  │ ✓ Negative Prompt              ✓ Batch Generation       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  Default Parameters:                                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ width: 1024   height: 1024   num_outputs: 1             │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  Tags: fast, general                                         │
│                                                             │
│  ── Benchmarks ──────────────────────────────────────────── │
│  Avg Quality: 7.8/10   (12 runs)      [Run Benchmark]       │
│  Avg Latency: 1,230ms                                       │
│  Avg Cost:    $0.002                                        │
│  ┌──────────────────────────┬───────┬───────┬──────┐        │
│  │ Prompt                    │ Qual  │ Lat   │ Cost │        │
│  ├──────────────────────────┼───────┼───────┼──────┤        │
│  │ A serene mountain...     │ 8.2   │ 2340  │ $0.002│       │
│  │ A futuristic cityscape   │ 7.5   │ 1890  │ $0.002│       │
│  └──────────────────────────┴───────┴───────┴──────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 Benchmark Comparison Page

```
┌─────────────────────────────────────────────────────────────┐
│  Model Comparison          [Add Model +]  [Run Suite]       │
├─────────────────────────────────────────────────────────────┤
│  Suite: Landscape Prompt Set (12 prompts)                   │
│                                                             │
│  ┌──────────────┬──────────┬──────────┬──────────┬────────┐ │
│  │              │ Flux Schn │ Flux Pro  │ SDXL     │ DALL-E │
│  ├──────────────┼──────────┼──────────┼──────────┼────────┤ │
│  │ Quality (10) │ █████▌7.8│ ████████▌│ ██████▌  │ █████  │ │
│  │              │          │ 9.1      │ 8.4      │ 7.2    │ │
│  │ Latency (ms) │ ██▌1230  │ █████▌4560│ ███▌2980│ █████▌ │ │
│  │              │          │          │          │ 5120   │ │
│  │ Cost (¢)     │ █▌0.2    │ █████▌5.0│ ██▌1.0   │ ██████▌│ │
│  │              │          │          │          │ 6.0    │ │
│  │ Composite    │ ★ 7.2    │ ★ 8.0    │ ★ 7.6    │ ★ 6.1  │ │
│  └──────────────┴──────────┴──────────┴──────────┴────────┘ │
│                                                             │
│  ── Per-Prompt Detail ────────────────────────────────────  │
│  [▼] "A serene mountain landscape at sunset"                │
│  ┌──────────┬──────────┬──────────┬──────────┬────────┐    │
│  │          │ Flux Schn │ Flux Pro  │ SDXL     │ DALL-E │    │
│  ├──────────┼──────────┼──────────┼──────────┼────────┤    │
│  │ Score    │ 8.2      │ 9.5      │ 8.8      │ 7.0    │    │
│  │ Latency  │ 2340     │ 5100     │ 3120     │ 5400   │    │
│  │ Preview  │ [img]    │ [img]    │ [img]    │ [img]  │    │
│  └──────────┴──────────┴──────────┴──────────┴────────┘    │
│                                                   [Export]  │
└─────────────────────────────────────────────────────────────┘
```

### 7.4 Benchmark Suite Detail

```
┌─────────────────────────────────────────────────────────────┐
│  Landscape Prompt Set (12 prompts)          [Run All]       │
├─────────────────────────────────────────────────────────────┤
│  Type: Image                                                │
│  Created: 2026-06-20                                        │
│                                                             │
│  Prompts:                                                    │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 1.  A serene mountain landscape at sunset               │ │
│  │ 2.  A futuristic cityscape with neon lights             │ │
│  │ 3.  An abandoned castle in a misty forest               │ │
│  │ 4.  A tropical beach at golden hour                     │ │
│  │ ...                                                     │ │
│  │ 12. A field of lavender with a barn in the distance     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  Last Run: 2026-06-21 (3 models, 36 runs)                   │
│  [View Results →]                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Integration with Sprint 6 Media Layer

### 8.1 What Changes in the Sprint 6 Design

The Sprint 6 design (`docs/sprint-6-media-layer-design.md`) currently has hardcoded model maps in adapters. With the Model Registry, the updated flow is:

**Port changes** — `MediaRequest.model` becomes resolved via the registry:
```python
@dataclass
class MediaRequest:
    prompt: str
    media_type: str
    # model is now a resolved provider_model_id, looked up from registry
    provider_model_id: str
    provider: str
    # ... other fields unchanged
```

**Adapter changes** — adapters no longer carry `MODELS` dicts:
```python
class ReplicateMediaAdapter(MediaPort):
    name = "replicate"

    def generate(self, request: MediaRequest) -> MediaResult:
        # request.provider_model_id is already resolved
        # e.g., "black-forest-labs/flux-schnell"
        output = replicate.run(request.provider_model_id, input={...})
```

**Service changes** — `MediaService` queries the registry:
```python
class MediaService:
    def __init__(self, ..., model_registry: ModelRegistryService):
        self.model_registry = model_registry

    def _resolve_model(self, model_slug: str) -> Model:
        """Resolve user-facing model name to registered model."""
        model = self.model_registry.get(model_slug)
        if not model or model.status != "active":
            raise ValueError(f"Model '{model_slug}' not available")
        return model
```

### 8.2 Seed Data

On first launch, the registry is populated with known models via `seed.py`:

```python
SEED_MODELS = [
    {
        "provider": "replicate",
        "provider_model_id": "black-forest-labs/flux-schnell",
        "name": "Flux Schnell",
        "family": "flux",
        "media_types": ["image"],
        "capabilities": {"max_width": 1024, "max_height": 1024, "supports_seed": True},
        "default_params": {"width": 1024, "height": 1024},
        "cost_per_unit": 0.002, "cost_unit": "per_image",
        "tags": ["fast", "general"],
    },
    {
        "provider": "replicate",
        "provider_model_id": "black-forest-labs/flux-pro",
        "name": "Flux Pro",
        "family": "flux",
        "media_types": ["image"],
        "capabilities": {"max_width": 1440, "max_height": 1440, "supports_seed": True, "supports_negative_prompt": True},
        "default_params": {"width": 1024, "height": 1024},
        "cost_per_unit": 0.050, "cost_unit": "per_image",
        "tags": ["premium", "high-quality"],
    },
    {
        "provider": "replicate",
        "provider_model_id": "stability-ai/sdxl",
        "name": "SDXL",
        "family": "sdxl",
        "media_types": ["image"],
        "capabilities": {"max_width": 1024, "max_height": 1024, "supports_seed": True, "supports_negative_prompt": True},
        "default_params": {"width": 1024, "height": 1024},
        "cost_per_unit": 0.010, "cost_unit": "per_image",
        "tags": ["general", "open-source"],
    },
    # Future providers can be added as stubs
    {
        "provider": "openai",
        "provider_model_id": "dall-e-3",
        "name": "DALL-E 3",
        "family": "dall-e",
        "media_types": ["image"],
        "status": "coming_soon",
        "capabilities": {"max_width": 1792, "max_height": 1024},
        "default_params": {"width": 1024, "height": 1024},
        "tags": ["premium"],
    },
]
```

### 8.3 Progressive Enhancement

| Scenario | Behavior |
|----------|----------|
| Model Registry DB is empty | Seed data inserted on first service init |
| Unknown model requested | Service returns `{"error": "Model 'x' not found"}` |
| Model exists but adapter not installed | `is_available()` on adapter returns False; registry shows status but service refuses |
| New Replicate model released | User registers via API or seed update; no code change |
| Model deprecated | `status=deprecated`; selector deprioritizes; warning in response |

---

## 9. Files Changed/Added (14 files)

### New Files (11)

| # | File | Purpose |
|---|------|---------|
| 1 | `toll/ports/model_registry.py` | `Model` dataclass, `ModelRegistryPort` abstract |
| 2 | `toll/ports/benchmark.py` | `BenchmarkRun`, `BenchmarkSuite` dataclasses |
| 3 | `toll/model_registry/__init__.py` | Package init |
| 4 | `toll/model_registry/service.py` | `ModelRegistryService` — register, list, query, find_best |
| 5 | `toll/model_registry/repository.py` | `ModelRepository` — SQL CRUD |
| 6 | `toll/model_registry/seed.py` | Seed data for known models |
| 7 | `toll/benchmark/__init__.py` | Package init |
| 8 | `toll/benchmark/service.py` | `BenchmarkService` — run, compare, leaderboard |
| 9 | `toll/benchmark/repository.py` | `BenchmarkRepository` — SQL CRUD |
| 10 | `toll/benchmark/runner.py` | `BenchmarkRunner` — orchestrate generation + measurement |
| 11 | `toll/benchmark/quality_scorer.py` | `QualityScorer` — AI-based quality evaluation |

### Modified Files (3)

| # | File | Change |
|---|------|--------|
| 12 | `toll/core/feature_flags.py` | Register 4 model registry + benchmark flags |
| 13 | `toll/model/migrations/0011_model_registry.sql` | models, model_tags, benchmark_suites, benchmark_runs tables |
| 14 | `toll/application/handler_registry.py` | Register `model_register`, `model_list`, `benchmark_run` handlers |

---

## 10. Feature Flags

```python
# Model Registry & Benchmark — Sprint 6A
"model_registry": True,          # model registry subsystem (enabled by default)
"model_registry_seed": True,     # auto-seed known models on init
"benchmark_lab": False,          # benchmark subsystem (opt-in)
"benchmark_auto_quality": False, # AI-based quality scoring in benchmarks
```

**Rationale for defaults:**
- `model_registry: True` — the registry replaces hardcoded model maps; all Sprint 6 code depends on it
- `model_registry_seed: True` — without seed data, there are no models; seed is essential for MVP
- `benchmark_lab: False` — benchmarking is a power-user/admin feature; not needed for basic media generation
- `benchmark_auto_quality: False` — AI quality scoring costs tokens and may be noisy; opt-in

---

## 11. Handler Registration

```python
# In handler_registry.py:

# Model Registry
if flags.is_enabled("model_registry"):
    svc = ModelRegistryService(cm=cm)
    wf_engine.register_handler("model_register", svc.register_handler)
    wf_engine.register_handler("model_list", svc.list_handler)

# Benchmark Lab
if flags.is_enabled("benchmark_lab"):
    bench = BenchmarkService(cm=cm, model_registry=svc, media_service=media_svc)
    wf_engine.register_handler("benchmark_run", bench.run_handler)
    wf_engine.register_handler("benchmark_compare", bench.compare_handler)
```

---

## 12. Effect on Sprint 6 Media Layer Design

The Model Registry changes the Sprint 6 design in these specific ways:

| Sprint 6 Design Element | Change |
|------------------------|--------|
| `ReplicateMediaAdapter.MODELS` | Replaced — adapters no longer carry model lists |
| `MediaRequest.model` | Resolved via registry instead of raw string |
| `ProviderSelector._quality_score` | Can now draw from benchmark data instead of hardcoded scores |
| `MediaService._resolve_model()` | New method to lookup model before generation |
| `handler_registry.py` | Adds `model_register`, `model_list` handlers |
| Feature flags | Adds 4 new flags under Sprint 6A group |

**The Sprint 6 doc should be updated to reference the Model Registry for model resolution, removing hardcoded `MODELS` dicts from adapter classes.**

---

## 13. Edge Cases & Error Handling

| Scenario | Handling |
|----------|----------|
| Register duplicate model | `UNIQUE(provider, provider_model_id)` constraint → 409 Conflict |
| Register with empty provider | Validation error: provider required |
| Query non-existent model | `get()` returns None → 404 |
| Deprecated model used in generation | Service warns but allows; selector deprioritizes |
| Benchmark on unavailable model | Runner returns error run with `error` field; quality=0 |
| Large benchmark suite (1000 prompts) | Paginated run creation; async for long suites |
| No benchmark data for comparison | Empty results array, not an error |
| Quality scorer fails | `quality_score_auto` remains 0; run still persists |
| Seed data conflicts with existing | `INSERT OR IGNORE` — existing rows preserved |
| Provider discontinues a model | Admin sets `status=disabled` via API |
| Cost data unknown | `cost_per_unit=null`; cost_cents skipped in benchmark |

---

## 14. Test Plan (24 tests)

### Unit Tests (14)

| # | Test | File |
|---|------|------|
| 1 | `Model` dataclass default values | `tests/ports/test_model_registry.py` |
| 2 | `ModelRegistryService.register()` creates row | `tests/model_registry/test_service.py` |
| 3 | `ModelRegistryService.register()` rejects duplicate | `tests/model_registry/test_service.py` |
| 4 | `ModelRegistryService.get()` returns model | `tests/model_registry/test_service.py` |
| 5 | `ModelRegistryService.get()` returns None for missing | `tests/model_registry/test_service.py` |
| 6 | `ModelRegistryService.list()` filters by provider | `tests/model_registry/test_service.py` |
| 7 | `ModelRegistryService.list()` filters by media_type | `tests/model_registry/test_service.py` |
| 8 | `ModelRegistryService.disable()` sets status | `tests/model_registry/test_service.py` |
| 9 | `ModelRegistryService.find_best()` returns top model | `tests/model_registry/test_service.py` |
| 10 | `BenchmarkRun` dataclass | `tests/ports/test_benchmark.py` |
| 11 | `BenchmarkService.run_single()` creates run | `tests/benchmark/test_service.py` |
| 12 | `BenchmarkService.run_suite()` executes all prompts | `tests/benchmark/test_service.py` |
| 13 | `BenchmarkService.compare()` aggregates correctly | `tests/benchmark/test_service.py` |
| 14 | `BenchmarkRunner.execute()` captures timing | `tests/benchmark/test_runner.py` |

### Integration Tests (6)

| # | Test | File |
|---|------|------|
| 15 | Full register → list → get flow via SQLite | `tests/model_registry/test_integration.py` |
| 16 | Seed data populates empty DB | `tests/model_registry/test_integration.py` |
| 17 | Benchmark run with real model produces output file | `tests/benchmark/test_integration.py` |
| 18 | Compare endpoint with two models returns sorted | `tests/benchmark/test_integration.py` |
| 19 | Feature flag gating disables handlers | `tests/api/test_model_registry_api.py` |
| 20 | API: POST /api/models/register returns 201 | `tests/api/test_model_registry_api.py` |

### Repository Tests (4)

| # | Test | File |
|---|------|------|
| 21 | `ModelRepository` CRUD operations | `tests/model_registry/test_repository.py` |
| 22 | `ModelRepository` filter chaining | `tests/model_registry/test_repository.py` |
| 23 | `BenchmarkRepository` create + list | `tests/benchmark/test_repository.py` |
| 24 | `BenchmarkRepository` aggregation queries | `tests/benchmark/test_repository.py` |

---

## 15. Implementation Order (3 Phases)

### Phase 1 — Schema & Repository (Day 1–2)
1. `toll/model/migrations/0011_model_registry.sql` — all 4 tables
2. `toll/ports/model_registry.py` — `Model` dataclass
3. `toll/ports/benchmark.py` — `BenchmarkRun`, `BenchmarkSuite` dataclasses
4. `toll/model_registry/repository.py` — SQL CRUD with filtering
5. `toll/benchmark/repository.py` — SQL CRUD with aggregation
6. `toll/core/feature_flags.py` — register 4 flags
7. Tests for repositories + dataclasses

### Phase 2 — Services (Day 3–4)
8. `toll/model_registry/service.py` — register, list, query, find_best
9. `toll/model_registry/seed.py` — known model seed data
10. `toll/benchmark/quality_scorer.py` — AI quality evaluation
11. `toll/benchmark/runner.py` — benchmark execution harness
12. `toll/benchmark/service.py` — run, compare, leaderboard
13. `toll/application/handler_registry.py` — register handlers
14. Tests for services

### Phase 3 — Integration & Cleanup (Day 5)
15. Wire up API endpoints (FastAPI router)
16. Update `toll/application/media_service.py` to use registry for model resolution
17. Remove hardcoded `MODELS` dicts from adapter classes in Sprint 6
18. Full integration tests
19. Edge case hardening (duplicate registration, missing model, benchmark failures)

---

## 16. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Registry becomes stale (models exist in provider but not in DB) | Medium | Medium | Seed update cycle; API for manual registration |
| Quality scoring is unreliable | High | Medium | Human score override field; benchmark data is advisory, not authoritative |
| Benchmark generation costs accumulate | Medium | Low | Benchmarks are opt-in (`benchmark_lab: False`); cost tracking in each run |
| Model lookup becomes bottleneck | Low | Low | SQLite with index; future in-memory cache if needed |
| Provider changes model API | Medium | High | Provider abstraction in adapter; registry stores provider_model_id as opaque string |

---

## 17. Future Considerations (Post-Sprint 6A)

- **Model version pinning** — pin to specific model version/hash for reproducibility
- **Custom model registration** — user-trained LoRAs/adapters registered as models
- **Scheduled benchmarks** — cron-style periodic benchmark runs for regression detection
- **Benchmark report export** — HTML/PDF report with charts from comparison data
- **Model recommendations** — `find_best()` returns ranked list with explanation
- **Provider auth per model** — some models may require separate API keys
- **Cost tracking over time** — aggregate cost across all benchmark runs
- **Community benchmark leaderboard** — share benchmark results between instances
- **Benchmark prompt templates** — reusable prompt templates with variables
- **Cache benchmark results** — identical prompt+model+seed returns cached run
