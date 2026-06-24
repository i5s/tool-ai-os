"""Authentication models."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: str
    email: str
    username: str
    hashed_password: str
    role: str  # admin, tester, viewer
    is_active: bool = True
    created_at: str | None = None

    @staticmethod
    def now() -> str:
        return datetime.utcnow().isoformat() + "Z"

    def to_insert(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "hashed_password": self.hashed_password,
            "role": self.role,
            "is_active": 1 if self.is_active else 0,
            "created_at": self.created_at or self.now(),
            "updated_at": self.now(),
        }


@dataclass
class Session:
    id: str
    user_id: str
    token_hash: str
    expires_at: str
    created_at: str | None = None

    @staticmethod
    def now() -> str:
        return datetime.utcnow().isoformat() + "Z"

    def to_insert(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "token_hash": self.token_hash,
            "expires_at": self.expires_at,
            "created_at": self.created_at or self.now(),
        }
