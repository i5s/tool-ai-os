CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    title TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    parent_artifact_id TEXT,
    workflow_id TEXT,
    conversation_id TEXT,
    content TEXT NOT NULL DEFAULT '{}',
    rendered_path TEXT,
    preview_url TEXT,
    provider TEXT,
    model TEXT,
    intent TEXT,
    workspace_type TEXT,
    workspace_id TEXT,
    tags TEXT DEFAULT '[]',
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    expires_at TEXT,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id),
    FOREIGN KEY (parent_artifact_id) REFERENCES artifacts(id)
);

CREATE INDEX IF NOT EXISTS idx_artifacts_parent ON artifacts(parent_artifact_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_workflow ON artifacts(workflow_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_expires ON artifacts(expires_at);
