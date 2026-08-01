# platform/backend/Dockerfile
#
# Build context is the REPO ROOT (see platform/docker-compose.yml's
# `build.context: ..`), not this directory — needed so this image can
# `pip install` both the root `eadadl` package (attack/, detections/) and
# this backend package. See README.md "Why a path dependency".
#
# STATUS: written, not built — no local Docker install (see ROADMAP.md
# "Known blockers"; same no-admin-rights story as Packer/QEMU).

FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml /app/eadadl-src/pyproject.toml
COPY attack /app/eadadl-src/attack
COPY detections /app/eadadl-src/detections
RUN pip install --no-cache-dir /app/eadadl-src

COPY platform/backend/pyproject.toml /app/backend/pyproject.toml
COPY platform/backend/app /app/backend/app
RUN pip install --no-cache-dir /app/backend

WORKDIR /app/backend
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
