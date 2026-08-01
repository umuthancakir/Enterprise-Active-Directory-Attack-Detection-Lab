from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import hash_password
from app.bootstrap import ensure_bootstrap_user
from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import User


@pytest.fixture()
def db_sessionmaker() -> Generator[sessionmaker[Session]]:
    # In-memory SQLite, fresh per test — StaticPool keeps the same
    # connection alive for the whole test (in-memory SQLite is otherwise
    # dropped between connections).
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def client(db_sessionmaker: sessionmaker[Session]) -> Generator[TestClient]:
    def override_get_db() -> Generator[Session]:
        db = db_sessionmaker()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db = db_sessionmaker()
    ensure_bootstrap_user(db)
    db.close()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def viewer_user(db_sessionmaker: sessionmaker[Session]) -> None:
    """A second account with role='viewer', for RBAC tests — the bootstrap
    account (`client` fixture) is always 'operator'."""
    db = db_sessionmaker()
    db.add(User(username="viewer1", hashed_password=hash_password("viewer-pass"), role="viewer"))
    db.commit()
    db.close()


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/auth/login", data={"username": username, "password": password})
    assert response.status_code == 200
    token: str = response.json()["access_token"]
    return token


@pytest.fixture()
def operator_token(client: TestClient) -> str:
    return _login(client, settings.backend_admin_username, settings.backend_admin_password)


@pytest.fixture()
def auth_headers(operator_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {operator_token}"}


@pytest.fixture()
def viewer_headers(client: TestClient, viewer_user: None) -> dict[str, str]:
    token = _login(client, "viewer1", "viewer-pass")
    return {"Authorization": f"Bearer {token}"}
