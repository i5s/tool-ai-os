-- Sprint 2: Memory Graph + Workspace Manager + Conversations

-- Memory Graph
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN ('global', 'brand', 'university', 'project', 'knowledge')),
    entity_id TEXT,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    importance_score INTEGER NOT NULL DEFAULT 5 CHECK(importance_score BETWEEN 1 AND 10),
    source TEXT NOT NULL DEFAULT 'unknown',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_accessed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_memories_unique ON memories(type, entity_id, key);
CREATE INDEX IF NOT EXISTS idx_memories_type_entity ON memories(type, entity_id);
CREATE INDEX IF NOT EXISTS idx_memories_accessed ON memories(last_accessed_at);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance_score);
CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key);

-- Workspaces
CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN ('brand', 'university', 'project')),
    name TEXT NOT NULL,
    metadata TEXT,  -- JSON
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Semesters (university-only)
CREATE TABLE IF NOT EXISTS semesters (
    id TEXT PRIMARY KEY,
    university_id TEXT NOT NULL,
    name TEXT NOT NULL,
    metadata TEXT,  -- JSON
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (university_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_semesters_university ON semesters(university_id);

-- Active workspace state per user
CREATE TABLE IF NOT EXISTS workspace_state (
    user_id TEXT PRIMARY KEY,
    active_brand_id TEXT,
    active_university_id TEXT,
    active_project_id TEXT,
    active_semester_id TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Conversations (separate from memories)
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    workspace_type TEXT,
    workspace_id TEXT,
    metadata TEXT,  -- JSON
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_conversations_workspace ON conversations(workspace_type, workspace_id);

-- Messages
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata TEXT,  -- JSON: type, html_files, etc.
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
