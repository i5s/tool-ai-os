-- Sprint X-7: Multi-Agent Runtime MVP

CREATE TABLE IF NOT EXISTS runtime_jobs (
    id                TEXT PRIMARY KEY,
    task_id           TEXT NOT NULL,
    council_session_id TEXT,
    status            TEXT NOT NULL DEFAULT 'pending',
    plan_text         TEXT,
    merged_result     TEXT,
    created_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    completed_at      TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (council_session_id) REFERENCES council_sessions(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS runtime_assignments (
    id                TEXT PRIMARY KEY,
    runtime_job_id   TEXT NOT NULL,
    task_fragment     TEXT NOT NULL,
    assigned_agent_id TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'pending',
    execution_id      TEXT,
    created_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    completed_at      TEXT,
    FOREIGN KEY (runtime_job_id) REFERENCES runtime_jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_agent_id) REFERENCES agents(id) ON DELETE RESTRICT,
    FOREIGN KEY (execution_id) REFERENCES agent_executions(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS runtime_results (
    id                 TEXT PRIMARY KEY,
    runtime_assignment_id TEXT NOT NULL,
    agent_id           TEXT NOT NULL,
    result             TEXT NOT NULL,
    metadata           TEXT,
    created_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (runtime_assignment_id) REFERENCES runtime_assignments(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS runtime_memory (
    id                 TEXT PRIMARY KEY,
    runtime_job_id     TEXT NOT NULL,
    memory_type        TEXT NOT NULL,
    content            TEXT NOT NULL,
    created_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (runtime_job_id) REFERENCES runtime_jobs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_runtime_jobs_task    ON runtime_jobs(task_id);
CREATE INDEX IF NOT EXISTS idx_runtime_jobs_status  ON runtime_jobs(status);
CREATE INDEX IF NOT EXISTS idx_runtime_jobs_council ON runtime_jobs(council_session_id);
CREATE INDEX IF NOT EXISTS idx_runtime_assignments_job ON runtime_assignments(runtime_job_id);
CREATE INDEX IF NOT EXISTS idx_runtime_assignments_agent ON runtime_assignments(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_runtime_results_assignment ON runtime_results(runtime_assignment_id);
CREATE INDEX IF NOT EXISTS idx_runtime_memory_job ON runtime_memory(runtime_job_id);
