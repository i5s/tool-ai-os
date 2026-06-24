"""User endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from toll.core.connection_manager import ConnectionManager
from api.routers.auth import router as auth_router
from toll.auth.service import AuthService
from toll.auth.dependencies import get_auth_service, require_roles
from toll.auth.repository import AuthRepository

router = APIRouter()


@router.get("/users")
def list_users(
        current=Depends(require_roles("admin")),
        service: AuthService = Depends(get_auth_service),
):
    repo = AuthRepository(cm=service.repo.cm)
    users = repo.cm.execute("SELECT id, email, username, role, is_active FROM users").fetchall()
    return [dict(row) for row in users]
