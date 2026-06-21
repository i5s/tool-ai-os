from pathlib import Path
from toll.adapters.media.fs_storage import FsMediaStorage


def test_save_creates_file(tmp_path):
    storage = FsMediaStorage(root=tmp_path)
    key = storage.save(b"hello", "images", "png")
    assert key.startswith("images/")
    assert key.endswith(".png")
    assert (tmp_path / key).exists()
    assert (tmp_path / key).read_bytes() == b"hello"


def test_get_path_returns_existing(tmp_path):
    storage = FsMediaStorage(root=tmp_path)
    key = storage.save(b"data", "images", "png")
    path = storage.get_path(key)
    assert path is not None
    assert path.exists()
    assert path.read_bytes() == b"data"


def test_get_path_returns_none_for_missing(tmp_path):
    storage = FsMediaStorage(root=tmp_path)
    path = storage.get_path("images/nonexistent.png")
    assert path is None


def test_delete_removes_file(tmp_path):
    storage = FsMediaStorage(root=tmp_path)
    key = storage.save(b"data", "images", "png")
    assert (tmp_path / key).exists()
    assert storage.delete(key)
    assert not (tmp_path / key).exists()


def test_delete_nonexistent_returns_false(tmp_path):
    storage = FsMediaStorage(root=tmp_path)
    assert not storage.delete("images/nonexistent.png")


def test_save_empty_data_raises(tmp_path):
    storage = FsMediaStorage(root=tmp_path)
    import pytest
    with pytest.raises(ValueError, match="empty data"):
        storage.save(b"", "images", "png")


def test_save_creates_subdirectory(tmp_path):
    storage = FsMediaStorage(root=tmp_path)
    key = storage.save(b"x", "video", "mp4")
    assert (tmp_path / "video").exists()
    assert (tmp_path / key).exists()


def test_default_root(tmp_path):
    storage = FsMediaStorage()
    assert storage.root.name == "media"
