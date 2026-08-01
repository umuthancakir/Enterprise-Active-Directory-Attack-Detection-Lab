"""JWT auth + role-based access control.

Two roles: "viewer" (read-only — GET endpoints) and "operator" (can also
trigger runs via POST /runs). This is deliberately minimal — no
self-service registration, no password reset flow, no per-scenario
permissions — because this is a single-operator lab
(docs/adr/0001-deploy-target.md's framing), not a multi-tenant product.
The one bootstrap account is created by app/bootstrap.py from
BACKEND_ADMIN_USERNAME/PASSWORD.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

ALGORITHM = "HS256"

# bcrypt's algorithm has a hard 72-byte input limit — truncating is
# standard practice (also what passlib did), not a shortcut introduced
# here. Using `bcrypt` directly rather than passlib's CryptContext: passlib
# 1.7.4's bcrypt backend self-test hashes a 250-byte probe string on first
# use to detect a legacy wraparound bug, and that self-test itself throws
# on bcrypt>=4.0's strict 72-byte enforcement — a real, currently-unfixed
# passlib/bcrypt version incompatibility, not something wrong with this
# code's own inputs. Discovered by the test suite actually exercising
# login, not by inspection.


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))


def create_access_token(username: str) -> str:
    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": username, "exp": expire}
    token: str = jwt.encode(payload, settings.backend_secret_key, algorithm=ALGORITHM)
    return token


_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: Annotated[str, Depends(_oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    try:
        payload = jwt.decode(token, settings.backend_secret_key, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise _credentials_exception
    except JWTError as exc:
        raise _credentials_exception from exc

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise _credentials_exception
    return user


def require_role(role: str) -> Callable[[User], User]:
    """Dependency factory: Depends(require_role("operator")) rejects any user
    without exactly that role with 403. Not hierarchical (operator doesn't
    imply viewer-plus) — deliberately explicit per-endpoint rather than
    clever, given there are only two roles."""

    def _check(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role '{role}', user has '{current_user.role}'",
            )
        return current_user

    return _check
