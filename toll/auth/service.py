"""Authentication service.

MVP scope only:
- password hashing via passlib/bcrypt
- session creation/validation/expiration
- login/logout/me
- default admin bootstrap
"""
from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from passlib.context import CryptContext

from .models import User, Session
from .repository import AuthRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SESSION_HOURS = int(os.getenv("TOLL_SESSION_HOURS", "12"))
DEFAULT_ADMIN_EMAIL = os.getenv("TOLL_ADMIN_EMAIL", "admin@example.com")
DEFAULT_ADMIN_PASSWORD = os.getenv("TOLL_ADMIN_PASSWORD", "toll-admin")
DEFAULT_ADMIN_USERNAME = os.getenv("TOLL_ADMIN_USERNAME", "admin")


class AuthService:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        return pwd_context.verify(password, hashed)

    def create_default_admin(self) -> User | None:
        existing = self.repo.get_user_by_email(DEFAULT_ADMIN_EMAIL)
        if existing:
            return None
        user = User(
            id=_uid(),
            email=DEFAULT_ADMIN_EMAIL,
            username=DEFAULT_ADMIN_USERNAME,
            hashed_password=self.hash_password(DEFAULT_ADMIN_PASSWORD),
            role="admin",
            is_active=True,
        )
        self.repo.create_user(user)
        return user

    def login(self, email: str, password: str, token: str) -> Optional[User]:
        record = self.repo.get_user_by_email(email)
        if not record:
            return None
        if not record["is_active"]:
            return None
        if not self.verify_password(password, record["hashed_password"]):
            return None

        user = _row_to_user(record)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=SESSION_HOURS)
        session = Session(
            id=_uid(),
            user_id=user.id,
            token_hash=self.hash_password(token),
            expires_at=expires.isoformat(),
        )
        self.repo.create_session(session)
        self.repo.delete_expired_sessions()
        return user

    def logout(self, token: str) -> None:
        unexpired = self.repo.get_unexpired_sessions()
        for record in unexpired:
            if self.verify_password(token, record["token_hash"]):
                self.repo.delete_session(record["id"])
                return

    def validate_session(self, token: str) -> User | None:
        unexpired = self.repo.get_unexpired_sessions()
        for record in unexpired:
            if self.verify_password(token, record["token_hash"]):
                user_record = self.repo.get_user_by_id(record["user_id"])
                if not user_record or not user_record["is_active"]:
                    return None
                return _row_to_user(user_record)
        return None


def _uid() -> str:
    return secrets.token_hex(12)


def _row_to_user(row: dict) -> User:
    return User(
        id=row["id"],
        email=row["email"],
        username=row["username"],
        hashed_password=row["hashed_password"],
        role=row["role"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
    )


def _is_expired(expires_at: str) -> bool:
    try:
        dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) > dt
    except Exception:
        return True
