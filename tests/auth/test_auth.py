"""Authentication tests."""
from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.dependencies import get_connection_manager
from toll.auth.service import AuthService
from toll.auth.repository import AuthRepository
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags


@pytest.fixture()
def cm(tmp_path: Any):
    db = tmp_path / "test.db"
    mgr = ConnectionManager(str(db))
    mgr.execute("PRAGMA journal_mode=WAL;")
    mgr.execute("PRAGMA foreign_keys = OFF;")
    flags = FeatureFlags(cm=mgr)
    flags.enable("auth")
    yield mgr
    mgr.close()


@pytest.fixture()
def client(cm: ConnectionManager):
    app.dependency_overrides[get_connection_manager] = lambda: cm
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_service(cm: ConnectionManager) -> AuthService:
    return AuthService(repo=AuthRepository(cm=cm))


def _bootstrap_admin(auth_service: AuthService) -> dict[str, Any]:
    user = auth_service.create_default_admin()
    assert user is not None, "Default admin bootstrap failed"
    return {"id": user.id, "email": user.email, "role": user.role}


def test_admin_bootstrap(auth_service: AuthService) -> None:
    user = _bootstrap_admin(auth_service)
    assert user["email"] == "admin@example.com"
    assert user["role"] == "admin"


def test_login_success(client: TestClient, auth_service: AuthService) -> None:
    _bootstrap_admin(auth_service)
    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "toll-admin"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["token"]
    assert data["email"] == "admin@example.com"
    assert data["role"] == "admin"
    assert data["user_id"]


def test_login_invalid_password(client: TestClient, auth_service: AuthService) -> None:
    _bootstrap_admin(auth_service)
    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "wrong"})
    assert response.status_code == 401


def test_session_created_after_login(client: TestClient, auth_service: AuthService) -> None:
    _bootstrap_admin(auth_service)
    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "toll-admin"})
    assert response.status_code == 200
    token = response.json()["token"]
    user = auth_service.validate_session(token)
    assert user is not None
    assert user.id == response.json()["user_id"]


def test_protected_endpoint_access(client: TestClient, auth_service: AuthService) -> None:
    _bootstrap_admin(auth_service)
    login_response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "toll-admin"})
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "admin@example.com"


def test_logout_invalidates_session(client: TestClient, auth_service: AuthService) -> None:
    _bootstrap_admin(auth_service)
    login_response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "toll-admin"})
    token = login_response.json()["token"]
    user_id = login_response.json()["user_id"]
    logout_response = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_response.status_code == 204
    user_after = auth_service.validate_session(token)
    assert user_after is None


def test_me_requires_token(client: TestClient) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401
