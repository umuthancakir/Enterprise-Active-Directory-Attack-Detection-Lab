# platform/

The platform layer: FastAPI backend + PostgreSQL + Next.js frontend,
running outside the lab network entirely (see root [README.md](../README.md)'s
architecture diagram). `make platform` (root `Makefile`) brings all three
up via `docker-compose.yml`.

| Component | Status |
|---|---|
| [`backend/`](backend/README.md) | **Fully tested** — 19/19 passing, `ruff`/`mypy --strict` clean |
| [`frontend/`](frontend/README.md) | Written, **not validated** — no local Node.js install (see root `ROADMAP.md`) |
| `docker-compose.yml` | Written, **not run** — no local Docker install |

## Why the backend could be tested and the frontend couldn't

Everything the backend needs (`fastapi`, `sqlalchemy`, `pytest`, ...) is
pip-installable at user level, no admin rights required — the same
discovery that unlocked real testing for `attack/`, `detections/`, and
`config/`'s Ansible earlier in this build (see root `BUILD_LOG.md`).
Node.js has no equivalent user-level install path; it needs Homebrew,
which needs admin rights this account doesn't have. So the backend is
held to this project's normal "verified, not just written" standard, and
the frontend is honestly flagged as the exception — see
`frontend/README.md`'s Status section for exactly what hasn't run.

## Quick start (once Docker is available)

```bash
cp ../.env.example ../.env   # fill in POSTGRES_*, BACKEND_*, NEXT_PUBLIC_*
make platform                 # from repo root
# API: http://localhost:8000/docs
# UI:  http://localhost:3000
```

Sign in with `BACKEND_ADMIN_USERNAME`/`BACKEND_ADMIN_PASSWORD` from `.env`
— that account is created automatically on first backend startup (see
`backend/app/bootstrap.py`).
