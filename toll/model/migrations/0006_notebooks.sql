-- NotebookLM Integration — Sprint 5B
-- Adds notebook, notebook_source, notebook_note, and notebook_snapshot tables.

CREATE TABLE IF NOT EXISTS notebooks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    workspace_type TEXT,
    workspace_id TEXT,
    source_count INTEGER NOT NULL DEFAULT 0,
    note_count INTEGER NOT NULL DEFAULT 0,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notebook_sources (
    id TEXT PRIMARY KEY,
    notebook_id TEXT NOT NULL,
    title TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT,
    content_type TEXT NOT NULL DEFAULT 'text/plain',
    char_count INTEGER NOT NULL DEFAULT 0,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notebook_notes (
    id TEXT PRIMARY KEY,
    notebook_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    source_ids TEXT NOT NULL DEFAULT '[]',
    tags TEXT NOT NULL DEFAULT '[]',
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notebook_snapshots (
    id TEXT PRIMARY KEY,
    notebook_id TEXT NOT NULL,
    label TEXT NOT NULL DEFAULT '',
    snapshot_data TEXT NOT NULL DEFAULT '{}',
    source_count INTEGER NOT NULL DEFAULT 0,
    note_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_notebook_sources_notebook ON notebook_sources(notebook_id);
CREATE INDEX IF NOT EXISTS idx_notebook_notes_notebook ON notebook_notes(notebook_id);
CREATE INDEX IF NOT EXISTS idx_notebook_snapshots_notebook ON notebook_snapshots(notebook_id);
CREATE INDEX IF NOT EXISTS idx_notebooks_workspace ON notebooks(workspace_type, workspace_id);

CREATE VIRTUAL TABLE IF NOT EXISTS notebook_notes_fts USING fts5(
    title, content, tags,
    content='notebook_notes',
    content_rowid='rowid'
);
