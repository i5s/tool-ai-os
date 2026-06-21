import pytest
from pathlib import Path
from toll.core.connection_manager import ConnectionManager


def test_opens_connection(temp_db_path):
    cm = ConnectionManager(temp_db_path)
    try:
        row = cm.connection.execute("SELECT 1").fetchone()
        assert row[0] == 1
    finally:
        cm.close()


def test_wal_mode_enabled(temp_db_path):
    cm = ConnectionManager(temp_db_path)
    try:
        row = cm.connection.execute("PRAGMA journal_mode").fetchone()
        assert row[0] == "wal"
    finally:
        cm.close()


def test_foreign_keys_enabled(temp_db_path):
    cm = ConnectionManager(temp_db_path)
    try:
        row = cm.connection.execute("PRAGMA foreign_keys").fetchone()
        assert row[0] == 1
    finally:
        cm.close()


def test_health_check_passes(temp_db_path):
    cm = ConnectionManager(temp_db_path)
    try:
        # health_check should not raise
        cm.health_check()
    finally:
        cm.close()


def test_concurrent_execute_succeeds(temp_db_path):
    cm = ConnectionManager(temp_db_path)
    try:
        cm.execute("CREATE TABLE IF NOT EXISTS t (x INTEGER)")
        cm.execute("INSERT INTO t VALUES (1)")
        cm.commit()
        row = cm.connection.execute("SELECT x FROM t").fetchone()
        assert row[0] == 1
    finally:
        cm.close()


def test_executemany_and_commit(temp_db_path):
    cm = ConnectionManager(temp_db_path)
    try:
        cm.execute("CREATE TABLE IF NOT EXISTS t (x INTEGER)")
        cm.executemany("INSERT INTO t VALUES (?)", [(1,), (2,), (3,)])
        cm.commit()
        rows = cm.connection.execute("SELECT COUNT(*) FROM t").fetchone()
        assert rows[0] == 3
    finally:
        cm.close()


def test_runs_migrations(temp_db_path):
    cm = ConnectionManager(temp_db_path)
    try:
        tables = cm.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        names = {r[0] for r in tables}
        assert "config" in names
        assert "workflows" in names
        assert "memories" in names
    finally:
        cm.close()


def test_close_and_reopen(temp_db_path):
    cm = ConnectionManager(temp_db_path)
    cm.execute("CREATE TABLE IF NOT EXISTS t (x INTEGER)")
    cm.close()

    cm2 = ConnectionManager(temp_db_path)
    try:
        row = cm2.connection.execute(
            "SELECT name FROM sqlite_master WHERE name='t'"
        ).fetchone()
        assert row is not None
    finally:
        cm2.close()


def test_executescript(temp_db_path):
    cm = ConnectionManager(temp_db_path)
    try:
        cm.executescript("CREATE TABLE IF NOT EXISTS a (x INTEGER); INSERT INTO a VALUES (42);")
        row = cm.connection.execute("SELECT x FROM a").fetchone()
        assert row[0] == 42
    finally:
        cm.close()


def test_health_check_fails_on_closed_connection(temp_db_path):
    cm = ConnectionManager(temp_db_path)
    cm.close()
    with pytest.raises(RuntimeError, match="ConnectionManager is closed"):
        cm.health_check()
