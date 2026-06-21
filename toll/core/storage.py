import sqlite3
from pathlib import Path
from . import config
from ..model.migrations.runner import MigrationRunner

class Storage:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path) if db_path else config.DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._migrate()
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

    def _migrate(self):
        runner = MigrationRunner(self.db_path)
        runner.migrate()

    def get_config(self, key, default=None):
        row = self.conn.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set_config(self, key, value):
        self.conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, str(value)))
        self.conn.commit()

    def log_usage(self, provider, action="ask"):
        self.conn.execute("INSERT INTO usage (provider, action) VALUES (?, ?)", (provider, action))
        self.conn.commit()

    def usage_today(self, provider):
        row = self.conn.execute(
            "SELECT COUNT(*) as c FROM usage WHERE provider = ? AND date(timestamp) = date('now')",
            (provider,)
        ).fetchone()
        return row["c"] if row else 0

    def save_history(self, engine, task, result=""):
        self.conn.execute("INSERT INTO history (engine, task, result) VALUES (?, ?, ?)", (engine, task, result))
        self.conn.commit()

    def history(self, limit=20):
        return self.conn.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
