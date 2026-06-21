CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    provider_model_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    version TEXT,
    family TEXT,
    media_types TEXT NOT NULL DEFAULT '["image"]',
    capabilities TEXT NOT NULL DEFAULT '{}',
    default_params TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'active',
    cost_per_unit REAL,
    cost_unit TEXT,
    metadata TEXT DEFAULT '{}',
    registered_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(provider, provider_model_id)
);

CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider);
CREATE INDEX IF NOT EXISTS idx_models_status ON models(status);
CREATE INDEX IF NOT EXISTS idx_models_family ON models(family);

CREATE TABLE IF NOT EXISTS model_tags (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(model_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_model_tags_tag ON model_tags(tag);

CREATE TABLE IF NOT EXISTS benchmark_suites (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    prompts TEXT NOT NULL,
    media_type TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS benchmark_runs (
    id TEXT PRIMARY KEY,
    suite_id TEXT REFERENCES benchmark_suites(id),
    model_id TEXT NOT NULL REFERENCES models(id),
    prompt TEXT NOT NULL,
    prompt_index INTEGER,
    media_type TEXT NOT NULL,
    provider_latency_ms INTEGER,
    total_duration_ms INTEGER,
    file_size_bytes INTEGER,
    quality_score_auto REAL,
    quality_score_human REAL,
    cost_cents REAL,
    seed INTEGER,
    output_storage_key TEXT,
    content_type TEXT,
    width INTEGER,
    height INTEGER,
    duration_ms INTEGER,
    error TEXT,
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_benchmark_runs_model ON benchmark_runs(model_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_runs_suite ON benchmark_runs(suite_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_runs_media ON benchmark_runs(media_type);
