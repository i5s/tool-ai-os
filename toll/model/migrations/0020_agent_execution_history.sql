CREATE TABLE IF NOT EXISTS agent_executions (
    id                TEXT PRIMARY KEY,
    task_id           TEXT NOT NULL,
    agent_id          TEXT NOT NULL,
    status            TEXT NOT NULL,
    started_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    completed_at      TEXT,
    duration_ms       INTEGER,
    stdout            TEXT,
    stderr            TEXT,
    execution_metadata TEXT,
    created_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_agent_executions_task_id   ON agent_executions(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_agent_id  ON agent_executions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_status    ON agent_executions(status);
CREATE INDEX IF NOT EXISTS idx_agent_executions_started  ON agent_executions(started_at);
