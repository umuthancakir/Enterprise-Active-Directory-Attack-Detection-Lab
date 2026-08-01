from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import settings


def test_login_with_correct_credentials_returns_token(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        data={
            "username": settings.backend_admin_username,
            "password": settings.backend_admin_password,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_with_wrong_password_returns_401(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        data={"username": settings.backend_admin_username, "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_login_with_unknown_username_returns_401(client: TestClient) -> None:
    response = client.post(
        "/auth/login", data={"username": "nobody", "password": "irrelevant"}
    )
    assert response.status_code == 401


def test_protected_endpoint_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/scenarios")
    assert response.status_code == 401


def test_protected_endpoint_with_bad_token_returns_401(client: TestClient) -> None:
    response = client.get("/scenarios", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_protected_endpoint_with_valid_token_succeeds(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/scenarios", headers=auth_headers)
    assert response.status_code == 200
