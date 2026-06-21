-- Sprint 5C: Research Memory Automation

-- Research memory metadata: links memories back to research artifacts
-- and tracks per-source importance signals
CREATE TABLE IF NOT EXISTS research_memory_meta (
    memory_id TEXT PRIMARY KEY,
    artifact_id TEXT,
    source_id TEXT,
    topic TEXT NOT NULL,
    keywords TEXT NOT NULL DEFAULT '[]',
    times_accessed INTEGER DEFAULT 0,
    times_retopic_hit INTEGER DEFAULT 0,
    last_boosted_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_research_memory_topic
    ON research_memory_meta(topic);
CREATE INDEX IF NOT EXISTS idx_research_memory_artifact
    ON research_memory_meta(artifact_id);
