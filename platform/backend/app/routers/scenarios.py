from __future__ import annotations

from typing import Annotated

from attack.chains import CHAINS
from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.models import User
from app.schemas import ScenarioSummary

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioSummary])
def list_scenarios(
    _current_user: Annotated[User, Depends(get_current_user)],
) -> list[ScenarioSummary]:
    return [
        ScenarioSummary(
            id=chain.id,
            description=chain.description,
            technique_ids=list(chain.technique_ids),
        )
        for chain in CHAINS.values()
    ]
