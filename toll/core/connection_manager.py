"""Thread-safe SQLite connection manager with health checks.

Single-user local-first design: uses ``check_same_thread=False``
to allow FastAPI thread-pool access, protected by a write lock.

Enforces:
- PRAGMA journal_mode = WAL
- PRAGMA foreign_keys = ON
- Migrations applied at startup
"""

import sqlite3
import threading
from pathlib import Path

from ..model.migrations.runner import MigrationRunner


class HealthCheckError(RuntimeError):
    """Raised when a health check fails at startup."""


class ConnectionManager:
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None
        self._open()

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def _open(self):
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._set_pragmas()
        self._run_migrations()

    def _set_pragmas(self):
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.commit()

    def _run_migrations(self):
        runner = MigrationRunner(self.db_path)
        runner.migrate()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def connection(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("ConnectionManager is closed")
        return self._conn

    # ------------------------------------------------------------------
    # Thread-safe execute helpers
    # ------------------------------------------------------------------

    def execute(self, sql: str, params=()) -> sqlite3.Cursor:
        with self._lock:
            return self.connection.execute(sql, params)

    def executemany(self, sql: str, seq) -> sqlite3.Cursor:
        with self._lock:
            return self.connection.executemany(sql, seq)

    def executescript(self, sql: str):
        with self._lock:
            self.connection.executescript(sql)

    def commit(self):
        with self._lock:
            self.connection.commit()

    # ------------------------------------------------------------------
    # Startup health check  — fail fast
    # ------------------------------------------------------------------

    def health_check(self):
        """Verify database is usable. Raises HealthCheckError on failure."""
        errors: list[str] = []

        # 1. Database reachable
        try:
            self.connection.execute("SELECT 1")
        except sqlite3.Error as e:
            errors.append(f"Database unreachable: {e}")

        # 2. Foreign keys enabled
        try:
            row = self.connection.execute("PRAGMA foreign_keys").fetchone()
            if not row or row[0] != 1:
                errors.append("Foreign keys are DISABLED (PRAGMA foreign_keys != 1)")
        except sqlite3.Error as e:
            errors.append(f"Cannot check foreign_keys pragma: {e}")

        # 3. WAL mode enabled
        try:
            row = self.connection.execute("PRAGMA journal_mode").fetchone()
            if not row or row[0].lower() != "wal":
                errors.append(
                    f"WAL mode is OFF (journal_mode={row[0] if row else 'unknown'})"
                )
        except sqlite3.Error as e:
            errors.append(f"Cannot check journal_mode pragma: {e}")

        # 4. All migrations applied
        try:
            runner = MigrationRunner(self.db_path)
            pending = runner.pending()
            if pending:
                errors.append(f"Pending migrations not applied: {pending}")
        except sqlite3.Error as e:
            errors.append(f"Cannot check migrations: {e}")

        if errors:
            raise HealthCheckError(
                "ConnectionManager health check FAILED:\n" + "\n".join(errors)
            )
