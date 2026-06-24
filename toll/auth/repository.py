"""Authentication data access."""
from __future__ import annotations

from typing import Any

from ..core.connection_manager import ConnectionManager
from .models import User, Session


class AuthRepository:
    def __init__(self, cm: ConnectionManager):
        self.cm = cm

    def get_user_by_email(self, email: str) -> dict | None:
        row = self.cm.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.lower(),),
        ).fetchone()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> dict | None:
        row = self.cm.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None

    def create_user(self, user: User) -> None:
        data = user.to_insert()
        self.cm.execute(
            "INSERT INTO users (id, email, username, hashed_password, role, is_active, created_at, updated_at) "
            "VALUES (:id, :email, :username, :hashed_password, :role, :is_active, :created_at, :updated_at)",
            data,
        )
        self.cm.commit()

    def create_session(self, session: Session) -> None:
        data = session.to_insert()
        self.cm.execute(
            "INSERT INTO sessions (id, user_id, token_hash, expires_at, created_at) "
            "VALUES (:id, :user_id, :token_hash, :expires_at, :created_at)",
            data,
        )
        self.cm.commit()

    def get_session_by_token_hash(self, token_hash: str) -> dict | None:
        row = self.cm.execute(
            "SELECT * FROM sessions WHERE token_hash = ?", (token_hash,)
        ).fetchone()
        return dict(row) if row else None

    def delete_session(self, session_id: str) -> None:
        self.cm.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self.cm.commit()

    def delete_expired_sessions(self) -> None:
        now = Session.now()
        self.cm.execute(
            "DELETE FROM sessions WHERE expires_at < ?",
            (now,),
        )
        self.cm.commit()

    def get_unexpired_sessions(self) -> list[dict]:
        now = Session.now()
        rows = self.cm.execute(
            "SELECT * FROM sessions WHERE expires_at >= ?",
            (now,),
        ).fetchall()
        return [dict(row) for row in rows]
