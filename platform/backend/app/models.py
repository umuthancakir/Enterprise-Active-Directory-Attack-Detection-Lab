"""SQLAlchemy ORM models: users (RBAC), scenario runs, and their findings.

ScenarioRun/RunFinding mirror attack.finding.Finding's shape deliberately
— the API persists exactly what attack.runner.run_scenario() produces,
not a reshaped version of it, so a run triggered via the API and a run
triggered via `make attack` produce comparable records.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    # "viewer" (read-only) or "operator" (can trigger runs) — see app/auth.py.
    role: Mapped[str] = mapped_column(String, default="viewer")


class ScenarioRun(Base):
    __tablename__ = "scenario_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    scenario: Mapped[str] = mapped_column(String, index=True)
    mode: Mapped[str] = mapped_column(String)  # "dry_run" | "live"
    triggered_by: Mapped[str] = mapped_column(String)  # username
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.UTC)
    )

    findings: Mapped[list[RunFinding]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class RunFinding(Base):
    __tablename__ = "run_findings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(ForeignKey("scenario_runs.id"), index=True)

    technique_id: Mapped[str] = mapped_column(String)
    attack_id: Mapped[str] = mapped_column(String)
    attack_url: Mapped[str] = mapped_column(String)
    target_host_id: Mapped[str] = mapped_column(String)
    target_ip: Mapped[str] = mapped_column(String)
    tool: Mapped[str] = mapped_column(String)
    command: Mapped[str] = mapped_column(String)  # JSON-encoded list[str]
    status: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(String)
    raw_output: Mapped[str] = mapped_column(String)  # JSON-encoded

    run: Mapped[ScenarioRun] = relationship(back_populates="findings")
