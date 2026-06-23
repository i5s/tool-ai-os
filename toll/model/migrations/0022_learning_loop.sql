-- Sprint X-5: Learning Loop MVP

CREATE TABLE IF NOT EXISTS learning_entries (
    id           TEXT PRIMARY KEY,
    source_type  TEXT NOT NULL,
    source_id    TEXT NOT NULL,
    agent_id     TEXT NOT NULL,
    title        TEXT NOT NULL,
    lesson       TEXT NOT NULL,
    confidence   REAL NOT NULL,
    created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS learning_feedback (
    id               TEXT PRIMARY KEY,
    learning_entry_id TEXT NOT NULL,
    feedback_type    TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    FOREIGN KEY (learning_entry_id) REFERENCES learning_entries(id)
);

CREATE INDEX IF NOT EXISTS idx_learning_entries_source ON learning_entries(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_learning_entries_agent ON learning_entries(agent_id);
CREATE INDEX IF NOT EXISTS idx_learning_feedback_entry ON learning_feedback(learning_entry_id);
