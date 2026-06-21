CREATE TABLE IF NOT EXISTS prompt_profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    media_types TEXT NOT NULL DEFAULT '["image"]',
    template TEXT NOT NULL DEFAULT '',
    default_params TEXT NOT NULL DEFAULT '{}',
    compatible_models TEXT NOT NULL DEFAULT '[]',
    weight_criteria TEXT NOT NULL DEFAULT '{}',
    tags TEXT NOT NULL DEFAULT '[]',
    version INTEGER NOT NULL DEFAULT 1,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_prompt_profiles_media ON prompt_profiles(media_types);
CREATE INDEX IF NOT EXISTS idx_prompt_profiles_tags ON prompt_profiles(tags);

CREATE TABLE IF NOT EXISTS prompt_profile_versions (
    id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL REFERENCES prompt_profiles(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    template TEXT NOT NULL DEFAULT '',
    default_params TEXT NOT NULL DEFAULT '{}',
    changed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_prompt_versions_profile ON prompt_profile_versions(profile_id);

CREATE TABLE IF NOT EXISTS prompt_scores (
    id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL REFERENCES prompt_profiles(id),
    model_id TEXT NOT NULL,
    score REAL,
    prompt_hash TEXT,
    artifact_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_prompt_scores_profile ON prompt_scores(profile_id);
CREATE INDEX IF NOT EXISTS idx_prompt_scores_model ON prompt_scores(model_id);

CREATE TABLE IF NOT EXISTS prompt_blacklist (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    profile_id TEXT NOT NULL REFERENCES prompt_profiles(id),
    reason TEXT DEFAULT '',
    flagged_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(model_id, profile_id)
);

CREATE INDEX IF NOT EXISTS idx_prompt_blacklist_lookup ON prompt_blacklist(model_id, profile_id);
