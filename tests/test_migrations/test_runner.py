import sqlite3
from pathlib import Path
from toll.model.migrations.runner import MigrationRunner


def test_migration_applies_initial(temp_db_path):
    runner = MigrationRunner(temp_db_path)
    applied = runner.migrate()
    assert "0001_initial" in applied

    # Verify tables exist
    conn = sqlite3.connect(str(temp_db_path))
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    table_names = {row[0] for row in tables}
    assert "usage" in table_names
    assert "config" in table_names
    assert "history" in table_names
    assert "migrations" in table_names


def test_migration_is_idempotent(temp_db_path):
    runner = MigrationRunner(temp_db_path)
    first = runner.migrate()
    second = runner.migrate()
    assert "0001_initial" in first
    assert "0001_initial" not in second


def test_pending_returns_empty_after_migrate(temp_db_path):
    runner = MigrationRunner(temp_db_path)
    runner.migrate()
    assert runner.pending() == []
