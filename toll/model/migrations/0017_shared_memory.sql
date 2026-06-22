CREATE TABLE IF NOT EXISTS memory_blocks (
    id           TEXT PRIMARY KEY,
    type         TEXT NOT NULL,
    scope        TEXT NOT NULL,
    scope_id     TEXT,
    title        TEXT NOT NULL,
    content      TEXT,
    created_by   TEXT,
    metadata     TEXT,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_links (
    id          TEXT PRIMARY KEY,
    source_id   TEXT NOT NULL,
    target_id   TEXT NOT NULL,
    relation    TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES memory_blocks(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES memory_blocks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_memory_blocks_scope ON memory_blocks (scope, scope_id);
CREATE INDEX IF NOT EXISTS idx_memory_blocks_type   ON memory_blocks (type);
CREATE INDEX IF NOT EXISTS idx_memory_links_source   ON memory_links (source_id);
CREATE INDEX IF NOT EXISTS idx_memory_links_target   ON memory_links (target_id);
