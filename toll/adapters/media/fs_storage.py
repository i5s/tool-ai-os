from __future__ import annotations

import uuid
from pathlib import Path

from ...ports.media_storage import MediaStorage

MEDIA_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "data" / "media"


class FsMediaStorage(MediaStorage):
    def __init__(self, root: Path | None = None):
        self.root = root or MEDIA_ROOT

    def save(self, data: bytes, media_type: str, extension: str) -> str:
        if not data:
            raise ValueError("Cannot save empty data")
        subdir = self.root / media_type
        subdir.mkdir(parents=True, exist_ok=True)
        key = f"{uuid.uuid4()}.{extension}"
        path = subdir / key
        path.write_bytes(data)
        return f"{media_type}/{key}"

    def get_path(self, storage_key: str) -> Path | None:
        path = self.root / storage_key
        if path.exists():
            return path
        return None

    def delete(self, storage_key: str) -> bool:
        path = self.root / storage_key
        if path.exists():
            path.unlink()
            return True
        return False
