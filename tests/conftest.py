import pytest
from pathlib import Path
from toll.core.connection_manager import ConnectionManager
from toll.core.storage import Storage
from toll.core.feature_flags import FeatureFlags


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "toll_test.db"


@pytest.fixture
def cm(temp_db_path: Path) -> ConnectionManager:
    mgr = ConnectionManager(db_path=temp_db_path)
    yield mgr
    mgr.close()


@pytest.fixture
def storage(cm: ConnectionManager) -> Storage:
    return Storage(cm=cm)


@pytest.fixture
def feature_flags(cm: ConnectionManager) -> FeatureFlags:
    return FeatureFlags(cm=cm)
