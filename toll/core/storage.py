import sqlite3
from pathlib import Path
from .connection_manager import ConnectionManager


class Storage:
    def __init__(self, cm: ConnectionManager):
        self.cm = cm

    @property
    def conn(self) -> sqlite3.Connection:
        return self.cm.connection

    def get_config(self, key, default=None):
        row = self.conn.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set_config(self, key, value):
        self.cm.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, str(value)))
        self.cm.commit()

    def log_usage(self, provider, action="ask"):
        self.cm.execute("INSERT INTO usage (provider, action) VALUES (?, ?)", (provider, action))
        self.cm.commit()

    def usage_today(self, provider):
        row = self.conn.execute(
            "SELECT COUNT(*) as c FROM usage WHERE provider = ? AND date(timestamp) = date('now')",
            (provider,)
        ).fetchone()
        return row["c"] if row else 0

    def save_history(self, engine, task, result=""):
        self.cm.execute("INSERT INTO history (engine, task, result) VALUES (?, ?, ?)", (engine, task, result))
        self.cm.commit()

    def history(self, limit=20):
        return self.conn.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
