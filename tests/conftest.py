import pytest
from pathlib import Path
from toll.core.storage import Storage
from toll.core.feature_flags import FeatureFlags


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "toll_test.db"


@pytest.fixture
def storage(temp_db_path: Path) -> Storage:
    return Storage(db_path=temp_db_path)


@pytest.fixture
def feature_flags(storage: Storage) -> FeatureFlags:
    return FeatureFlags(storage=storage)
