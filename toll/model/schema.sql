CREATE TABLE IF NOT EXISTS usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    action TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engine TEXT NOT NULL,
    task TEXT NOT NULL,
    result TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Default config
INSERT OR IGNORE INTO config (key, value) VALUES ('daily_limit_opencode', '20');
INSERT OR IGNORE INTO config (key, value) VALUES ('daily_limit_ollama', '50');
INSERT OR IGNORE INTO config (key, value) VALUES ('ollama_model', 'qwen2.5');
INSERT OR IGNORE INTO config (key, value) VALUES ('opencode_bin', '');
INSERT OR IGNORE INTO config (key, value) VALUES ('website_path', '');
