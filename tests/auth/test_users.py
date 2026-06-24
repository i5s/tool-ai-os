"""Users / role tests."""
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


def test_users_requires_auth(client: TestClient) -> None:
    response = client.get("/api/users")
    assert response.status_code == 401


def test_users_requires_admin_role(client: TestClient, auth_service: AuthService) -> None:
    _bootstrap_admin(auth_service)
    response = client.get("/api/users", headers={"Authorization": "Bearer invalid"})
    assert response.status_code in (401, 403)


def test_users_accessible_by_admin(client: TestClient, auth_service: AuthService) -> None:
    _bootstrap_admin(auth_service)
    login_response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "toll-admin"})
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    response = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
