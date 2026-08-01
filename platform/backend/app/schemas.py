"""Pydantic request/response models — the API's actual contract, kept
separate from app/models.py's ORM shape (e.g. `command`/`raw_output` are
stored as JSON strings in SQLite but always serialized back to real
JSON/list types here, never leaked as raw strings to a client)."""

from __future__ import annotations

import datetime
from typing import Any, Literal

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class ScenarioSummary(BaseModel):
    id: str
    description: str
    technique_ids: list[str]


class RunRequest(BaseModel):
    scenario: str
    mode: Literal["dry_run", "live"] = "dry_run"


class FindingResponse(BaseModel):
    technique_id: str
    attack_id: str
    attack_url: str
    target_host_id: str
    target_ip: str
    tool: str
    command: list[str]
    status: str
    summary: str
    raw_output: Any


class RunResponse(BaseModel):
    id: str
    scenario: str
    mode: str
    triggered_by: str
    created_at: datetime.datetime
    findings: list[FindingResponse]


class RunSummaryResponse(BaseModel):
    id: str
    scenario: str
    mode: str
    triggered_by: str
    created_at: datetime.datetime
    finding_count: int
