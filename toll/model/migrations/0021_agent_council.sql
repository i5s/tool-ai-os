-- Sprint X-4: Agent Council MVP

CREATE TABLE IF NOT EXISTS council_sessions (
    id           TEXT PRIMARY KEY,
    task_id      TEXT,
    status       TEXT NOT NULL,
    strategy     TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS council_members (
    id          TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    agent_id    TEXT NOT NULL,
    role        TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES council_sessions(id),
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE TABLE IF NOT EXISTS council_votes (
    id          TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    agent_id    TEXT NOT NULL,
    vote        TEXT NOT NULL,
    confidence  REAL NOT NULL,
    created_at  TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES council_sessions(id),
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE TABLE IF NOT EXISTS council_decisions (
    id                  TEXT PRIMARY KEY,
    session_id          TEXT NOT NULL,
    winning_agent_id    TEXT,
    decision_summary    TEXT NOT NULL,
    rationale           TEXT NOT NULL,
    created_at          TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES council_sessions(id),
    FOREIGN KEY (winning_agent_id) REFERENCES agents(id)
);

CREATE INDEX IF NOT EXISTS idx_council_sessions_task ON council_sessions(task_id);
CREATE INDEX IF NOT EXISTS idx_council_sessions_status ON council_sessions(status);
CREATE INDEX IF NOT EXISTS idx_council_members_session ON council_members(session_id);
CREATE INDEX IF NOT EXISTS idx_council_votes_session ON council_votes(session_id);
CREATE INDEX IF NOT EXISTS idx_council_decisions_session ON council_decisions(session_id);
