"""EADADL platform backend entry point.

Run: uvicorn app.main:app --reload (dev) or via platform/docker-compose.yml.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap import ensure_bootstrap_user
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import auth, coverage, runs, scenarios


@asynccontextmanager
async def lifespan(_app: FastAPI) -> Any:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_bootstrap_user(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="EADADL Platform API",
    description="Scenario runner, run history, and ATT&CK coverage API for the EADADL lab.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.backend_cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(scenarios.router)
app.include_router(runs.router)
app.include_router(coverage.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
