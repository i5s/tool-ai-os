CREATE TABLE IF NOT EXISTS agent_reputation (
    agent_id          TEXT PRIMARY KEY,
    reputation_score  REAL NOT NULL DEFAULT 0.0,
    quality_score     REAL NOT NULL DEFAULT 0.0,
    speed_score       REAL NOT NULL DEFAULT 0.0,
    reliability_score REAL NOT NULL DEFAULT 0.0,
    learning_score    REAL NOT NULL DEFAULT 0.0,
    council_score     REAL NOT NULL DEFAULT 0.0,
    recommended_rank  TEXT NOT NULL DEFAULT 'worker',
    updated_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_agent_reputation_score ON agent_reputation(reputation_score DESC);
CREATE INDEX IF NOT EXISTS idx_agent_reputation_rank   ON agent_reputation(recommended_rank);
