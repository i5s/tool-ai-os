from toll.core.storage import Storage


def test_storage_uses_custom_db_path(temp_db_path):
    storage = Storage(db_path=temp_db_path)
    storage.set_config("test_key", "test_value")
    assert temp_db_path.exists()
    assert storage.get_config("test_key") == "test_value"


def test_config_default(storage: Storage):
    assert storage.get_config("missing_key", "default") == "default"


def test_usage_logging(storage: Storage):
    storage.log_usage("opencode", "ask")
    count = storage.usage_today("opencode")
    assert count == 1


def test_history(storage: Storage):
    storage.save_history("report", "test task", "result")
    rows = storage.history(limit=10)
    assert len(rows) == 1
    assert rows[0]["engine"] == "report"
