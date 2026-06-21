"""SQLite migration runner.

Migrations are SQL files named NNNN_description.sql in this directory.
They are applied in order and tracked in the `migrations` table.
"""

import sqlite3
from pathlib import Path

_MIGRATIONS_DIR = Path(__file__).resolve().parent


class MigrationRunner:
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tracking_table(self, conn: sqlite3.Connection):
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS migrations (
                name TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()

    def _applied(self, conn: sqlite3.Connection) -> set[str]:
        self._ensure_tracking_table(conn)
        rows = conn.execute("SELECT name FROM migrations").fetchall()
        return {row["name"] for row in rows}

    def _migration_files(self) -> list[Path]:
        files = sorted(_MIGRATIONS_DIR.glob("[0-9][0-9][0-9][0-9]_*.sql"))
        return files

    def migrate(self) -> list[str]:
        """Apply all pending migrations. Returns list of applied migration names."""
        applied: list[str] = []
        with self._connection() as conn:
            already_applied = self._applied(conn)
            for path in self._migration_files():
                name = path.stem
                if name in already_applied:
                    continue
                sql = path.read_text(encoding="utf-8")
                conn.executescript(sql)
                conn.execute("INSERT INTO migrations (name) VALUES (?)", (name,))
                conn.commit()
                applied.append(name)
        return applied

    def pending(self) -> list[str]:
        with self._connection() as conn:
            already_applied = self._applied(conn)
            return [
                path.stem
                for path in self._migration_files()
                if path.stem not in already_applied
            ]
