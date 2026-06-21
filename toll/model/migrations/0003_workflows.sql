-- Sprint 3: Planner + Workflow Engine

CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    plan TEXT NOT NULL,  -- JSON
    status TEXT NOT NULL CHECK(status IN ('pending', 'approved', 'rejected', 'running', 'workflow_completed', 'workflow_failed')),
    result TEXT,  -- JSON
    error TEXT,
    metadata TEXT,  -- JSON
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
CREATE INDEX IF NOT EXISTS idx_workflows_updated ON workflows(updated_at);
