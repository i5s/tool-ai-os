CREATE TABLE IF NOT EXISTS agents (
    id               TEXT PRIMARY KEY,
    name             TEXT NOT NULL,
    role             TEXT NOT NULL,
    rank             TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'active',
    provider         TEXT NOT NULL DEFAULT '',
    model            TEXT NOT NULL DEFAULT '',
    cost_tier        TEXT NOT NULL DEFAULT 'standard',
    reputation_score REAL NOT NULL DEFAULT 0.0,
    quality_score    REAL NOT NULL DEFAULT 0.0,
    speed_score      REAL NOT NULL DEFAULT 0.0,
    created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS ix_agents_role ON agents(role);
CREATE INDEX IF NOT EXISTS ix_agents_rank ON agents(rank);
CREATE INDEX IF NOT EXISTS ix_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS ix_agents_provider ON agents(provider);
