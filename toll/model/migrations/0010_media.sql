CREATE TABLE IF NOT EXISTS media_meta (
    id TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL,
    media_type TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT,
    prompt TEXT NOT NULL,
    negative_prompt TEXT,
    width INTEGER,
    height INTEGER,
    duration_ms INTEGER,
    file_size_bytes INTEGER NOT NULL,
    content_type TEXT NOT NULL,
    seed INTEGER,
    style TEXT,
    error TEXT,
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_media_artifact_id ON media_meta(artifact_id);
CREATE INDEX IF NOT EXISTS idx_media_type ON media_meta(media_type);

CREATE TABLE IF NOT EXISTS media_resources (
    id TEXT PRIMARY KEY,
    source_media_id TEXT NOT NULL,
    derived_media_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (source_media_id) REFERENCES media_meta(id),
    FOREIGN KEY (derived_media_id) REFERENCES media_meta(id)
);
