"""Settings loaded from environment (.env at repo root — see .env.example).

Uses pydantic-settings so every value is validated at startup rather than
failing lazily the first time something reads a missing/malformed env var.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    # SQLite by default (zero-setup for tests/dev); .env.example's
    # POSTGRES_* vars compose a real DATABASE_URL for `make platform`'s
    # docker-compose deployment — see platform/docker-compose.yml.
    database_url: str = f"sqlite:///{REPO_ROOT / 'platform' / 'backend' / 'eadadl.db'}"

    backend_secret_key: str = "insecure-dev-only-key-see-.env.example"
    backend_cors_origins: str = "http://localhost:3000"

    # Bootstrap operator account, created on startup if no users exist yet
    # — see app/bootstrap.py. Not a general-purpose user-management system;
    # this is a single-operator lab (docs/adr/0001-deploy-target.md's
    # framing applies here too).
    backend_admin_username: str = "admin"
    backend_admin_password: str = "change-me-see-dot-env-example"

    access_token_expire_minutes: int = 60

    lab_scope_file: Path = REPO_ROOT / "inventory" / "lab-scope.yaml"
    coverage_matrix_file: Path = REPO_ROOT / "detections" / "coverage_matrix.json"


settings = Settings()
