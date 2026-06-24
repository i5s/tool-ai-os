"""Authentication endpoints."""
from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr

from toll.core.connection_manager import ConnectionManager
from toll.auth.dependencies import get_auth_service, require_auth
from toll.auth.models import User
from toll.auth.service import AuthService

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    user_id: str
    email: str
    username: str
    role: str
    token: str


class MeResponse(BaseModel):
    user_id: str
    email: str
    username: str
    role: str


@router.post("/auth/login", response_model=LoginResponse)
def login(
        payload: LoginRequest,
        response: Response,
        request: Request,
        service: AuthService = Depends(get_auth_service),
):
    token = secrets.token_hex(48)
    user = service.login(payload.email, payload.password, token)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    response.set_cookie(
        key="toll_session",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 12,
    )
    response.headers["X-TOKEN"] = token
    return LoginResponse(
        user_id=user.id, email=user.email, username=user.username, role=user.role, token=token
    )


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
        request: Request,
        response: Response,
        service: AuthService = Depends(get_auth_service),
):
    token = request.cookies.get("toll_session")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1].strip()
    if token:
        service.logout(token)
    response.delete_cookie("toll_session")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/auth/me", response_model=MeResponse)
def me(current=Depends(require_auth)):
    return MeResponse(user_id=current.user_id, email=current.email, username=current.username, role=current.role)

