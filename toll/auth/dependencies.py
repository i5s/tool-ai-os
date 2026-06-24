"""Authentication FastAPI dependencies."""
from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from api.dependencies import get_connection_manager
from .repository import AuthRepository
from .service import AuthService


def get_auth_service(cm: ConnectionManager = Depends(get_connection_manager)) -> AuthService:
    feature_flags = FeatureFlags(cm=cm)
    feature_flags.enable("auth")
    return AuthService(repo=AuthRepository(cm=cm))


class CurrentUser:
    def __init__(self, user_id: str, role: str, email: str, username: str):
        self.user_id = user_id
        self.role = role
        self.email = email
        self.username = username


def _extract_token(request: Request) -> str | None:
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return request.cookies.get("toll_session")


async def require_auth(request: Request, service: AuthService = Depends(get_auth_service)) -> CurrentUser:
    token = _extract_token(request)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = service.validate_session(token)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Session invalid or expired")
    return CurrentUser(user_id=user.id, role=user.role, email=user.email, username=user.username)


def require_roles(*roles: str):
    allowed = {r.lower() for r in roles}

    def _check(current: CurrentUser = Depends(require_auth)):
        if current.role.lower() not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current

    return _check
