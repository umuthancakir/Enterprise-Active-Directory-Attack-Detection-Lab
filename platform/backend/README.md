# platform/backend

FastAPI scenario runner, run history, and coverage API. Fully tested —
see "Status" below.

## Why a path dependency on the repo root

`app/routers/runs.py` and `app/routers/scenarios.py` import
`attack.runner`, `attack.lib.scope_guard`, and `attack.chains` directly —
POST `/runs` calls the exact same `run_scenario()` that `make attack`
does, gated by the exact same scope guard. Rather than vendor/copy that
code into the backend, this package depends on the repo-root `eadadl`
package as an editable install. Two install steps, not one:

```bash
cd "<repo root>"
pip install -e .                       # the eadadl package: attack/, detections/
cd platform/backend
pip install -e ".[dev]"                # this package + dev deps
```

(CI's `backend` job in `.github/workflows/ci.yml` does exactly this.)

## Auth / RBAC

Two roles — `viewer` (read-only) and `operator` (can also trigger runs).
One bootstrap account is created on first startup from
`BACKEND_ADMIN_USERNAME`/`BACKEND_ADMIN_PASSWORD` (`.env` — see
`app/config.py`). No self-service registration: this is a single-operator
lab (see `docs/adr/0001-deploy-target.md`'s framing), not a multi-tenant
product. See `app/auth.py`'s module docstring.

## Database

SQLite by default (zero-setup — `sqlite:///platform/backend/eadadl.db`,
gitignored), Postgres via `platform/docker-compose.yml`'s `DATABASE_URL`
for the real deployment. No Alembic migrations — `Base.metadata.create_all()`
runs at startup. Reasonable for a lab-scale app whose run-history data is
disposable alongside the lab itself (SECURITY.md #4); would need
migrations for anything longer-lived.

## Running locally

```bash
cd platform/backend
uvicorn app.main:app --reload
# API docs at http://localhost:8000/docs
```

`POST /runs` reads the real `inventory/lab-scope.yaml` (via
`app/config.py`'s `lab_scope_file`, same file `make attack`/`make
sync-scope` use) — on a fresh clone with nothing provisioned, it correctly
returns `403` (proven by `tests/test_runs.py::test_create_run_against_real_unprovisioned_scope_returns_403`,
which deliberately does NOT mock the scope file).

## Status

**Fully tested — 19/19 passing, `ruff` clean, `mypy --strict` clean (20
source files).** This is one of the few layers in this project that could
be validated end-to-end this session, since FastAPI/SQLAlchemy/pytest are
all pip-installable without admin rights (unlike Packer/QEMU/UTM — see
ROADMAP.md "Known blockers").

Found and fixed one real bug while getting tests green: `passlib`'s bcrypt
backend self-test is incompatible with `bcrypt>=4.0`'s strict 72-byte
input enforcement (a currently-unfixed passlib/bcrypt version mismatch,
not something wrong with this code's inputs) — switched to using `bcrypt`
directly instead of `passlib.CryptContext`. See `app/auth.py`'s comment.

**Not done:**

- No live lab exists, so `POST /runs` has only ever been exercised in
  `mode=dry_run` (the default) — `mode=live` goes through the exact same
  `attack.runner.run_scenario()` live path that's separately documented as
  unexercised in `ROADMAP.md`'s Phase 3 section.
- No rate limiting, no audit log of who ran what beyond the `triggered_by`
  field, no per-scenario permissions.
