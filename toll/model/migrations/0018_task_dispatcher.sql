CREATE TABLE IF NOT EXISTS tasks (
    id              TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    description     TEXT,
    status          TEXT NOT NULL DEFAULT 'draft',
    priority        TEXT NOT NULL DEFAULT 'medium',
    created_by      TEXT,
    assigned_agent_id TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    completed_at    TEXT
);

CREATE TABLE IF NOT EXISTS task_events (
    id          TEXT PRIMARY KEY,
    task_id     TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    actor       TEXT,
    payload     TEXT,
    created_at  TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tasks_status     ON tasks (status);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned   ON tasks (assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_events     ON task_events (task_id, created_at);
