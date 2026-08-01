"""Creates the bootstrap operator account if no users exist yet. See
app/auth.py's docstring for why there's no self-service registration."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.auth import hash_password
from app.config import settings
from app.models import User


def ensure_bootstrap_user(db: Session) -> None:
    if db.query(User).count() > 0:
        return
    db.add(
        User(
            username=settings.backend_admin_username,
            hashed_password=hash_password(settings.backend_admin_password),
            role="operator",
        )
    )
    db.commit()
