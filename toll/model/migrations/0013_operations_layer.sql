CREATE TABLE IF NOT EXISTS usage_log (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    model_id TEXT,
    media_type TEXT NOT NULL DEFAULT 'text',
    resource_type TEXT NOT NULL DEFAULT 'request',
    resource_count INTEGER NOT NULL DEFAULT 1,
    estimated_cost_cents REAL,
    duration_ms INTEGER,
    success INTEGER NOT NULL DEFAULT 1,
    error TEXT,
    artifact_id TEXT,
    profile_id TEXT,
    workspace_type TEXT,
    workspace_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_usage_created ON usage_log(created_at);
CREATE INDEX IF NOT EXISTS idx_usage_provider ON usage_log(provider);
CREATE INDEX IF NOT EXISTS idx_usage_model ON usage_log(model_id);

CREATE TABLE IF NOT EXISTS retention_policies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT 'Default',
    workspace_type TEXT,
    workspace_id TEXT,
    media_type TEXT,
    retention_days INTEGER NOT NULL DEFAULT 4,
    keep_metadata INTEGER NOT NULL DEFAULT 1,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT OR IGNORE INTO retention_policies (id, name, retention_days, keep_metadata, enabled)
VALUES ('default', 'Default Policy', 4, 1, 1);

CREATE TABLE IF NOT EXISTS cleanup_log (
    id TEXT PRIMARY KEY,
    policy_id TEXT REFERENCES retention_policies(id),
    artifact_id TEXT,
    action TEXT NOT NULL,
    file_size_bytes INTEGER,
    details TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
