"""POST /runs triggers attack.runner.run_scenario() against the real
inventory/lab-scope.yaml — the same scope guard that gates `make attack`
gates this endpoint too; there is no separate, less-safe path here. A
ScopeViolation (e.g. nothing provisioned) surfaces as 403, not a 500 or a
silently-empty run.
"""

from __future__ import annotations

import json
from typing import Annotated

from attack.chains import CHAINS
from attack.lib.scope_guard import ScopeViolation
from attack.runner import run_scenario
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.config import settings
from app.database import get_db
from app.models import RunFinding, ScenarioRun, User
from app.schemas import FindingResponse, RunRequest, RunResponse, RunSummaryResponse

router = APIRouter(prefix="/runs", tags=["runs"])


def _run_to_response(run: ScenarioRun) -> RunResponse:
    return RunResponse(
        id=run.id,
        scenario=run.scenario,
        mode=run.mode,
        triggered_by=run.triggered_by,
        created_at=run.created_at,
        findings=[
            FindingResponse(
                technique_id=f.technique_id,
                attack_id=f.attack_id,
                attack_url=f.attack_url,
                target_host_id=f.target_host_id,
                target_ip=f.target_ip,
                tool=f.tool,
                command=json.loads(f.command),
                status=f.status,
                summary=f.summary,
                raw_output=json.loads(f.raw_output),
            )
            for f in run.findings
        ],
    )


@router.post("", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
def create_run(
    body: RunRequest,
    current_user: Annotated[User, Depends(require_role("operator"))],
    db: Annotated[Session, Depends(get_db)],
) -> RunResponse:
    if body.scenario not in CHAINS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown scenario '{body.scenario}'. Known: {sorted(CHAINS)}",
        )

    try:
        # Explicit about which scope file gates this — same file `make
        # sync-scope`/`make attack` use (app/config.py's lab_scope_file
        # defaults to the real inventory/lab-scope.yaml), just passed
        # explicitly rather than relying on attack.runner's own default so
        # tests can point it elsewhere without touching the real file.
        findings = run_scenario(body.scenario, mode=body.mode, scope_file=settings.lab_scope_file)
    except ScopeViolation as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    run = ScenarioRun(scenario=body.scenario, mode=body.mode, triggered_by=current_user.username)
    run.findings = [
        RunFinding(
            technique_id=f.technique_id,
            attack_id=f.attack_id,
            attack_url=f.attack_url,
            target_host_id=f.target_host_id,
            target_ip=f.target_ip,
            tool=f.tool,
            command=json.dumps(f.command),
            status=f.status,
            summary=f.summary,
            raw_output=json.dumps(f.raw_output),
        )
        for f in findings
    ]
    db.add(run)
    db.commit()
    db.refresh(run)
    return _run_to_response(run)


@router.get("", response_model=list[RunSummaryResponse])
def list_runs(
    _current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[RunSummaryResponse]:
    runs = db.query(ScenarioRun).order_by(ScenarioRun.created_at.desc()).all()
    return [
        RunSummaryResponse(
            id=r.id,
            scenario=r.scenario,
            mode=r.mode,
            triggered_by=r.triggered_by,
            created_at=r.created_at,
            finding_count=len(r.findings),
        )
        for r in runs
    ]


@router.get("/{run_id}", response_model=RunResponse)
def get_run(
    run_id: str,
    _current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RunResponse:
    run = db.get(ScenarioRun, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return _run_to_response(run)
