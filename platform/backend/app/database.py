"""SQLAlchemy engine/session setup.

No Alembic migrations — `Base.metadata.create_all()` runs at startup
(app/main.py). A reasonable scope decision for a lab-scale app whose
schema is small and whose data (run history) is disposable alongside the
lab itself (SECURITY.md #4), not a production system that needs migration
history. Flagged in README.md rather than silently assumed acceptable.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
