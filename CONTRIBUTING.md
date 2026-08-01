# Contributing to EADADL

This is primarily a solo-built portfolio project, but it's structured to take
outside contributions cleanly. If you're contributing:

## Ground rules

- Read [SECURITY.md](SECURITY.md) first. Every safety invariant listed there
  is non-negotiable — PRs that weaken the scope guard, add an "arbitrary
  target" override, introduce novel exploit/evasion code, or remove network
  isolation will be rejected regardless of other merits.
- Every attack technique added under `attack/` must cite a published MITRE
  ATT&CK ID and reference link, and must orchestrate an established
  open-source tool rather than implement new offensive code.
- Every technique added under `attack/` should ship with (or open a tracked
  follow-up issue for) a corresponding Sigma rule under `detections/` and a
  test proving it fires against that technique's telemetry.

## Workflow

1. Open an issue describing the change before large PRs — especially for new
   infra components or attack chains.
2. Keep PRs scoped to one phase/component where possible.
3. Run the relevant checks locally before opening a PR:
   - `terraform fmt -check` / `terraform validate` for anything under `infra/`
   - `ansible-lint` for anything under `config/`
   - Sigma rule validation + `make detections-test` for anything under
     `detections/`
   - Backend: `pytest`, `ruff`, `mypy` under `platform/backend/`
   - Frontend: `npm run lint`, `npm run typecheck`, `npm test` under
     `platform/frontend/`
4. Update `docs/vulnerabilities.md` if you add or change an intentional lab
   misconfiguration, and `ROADMAP.md`/`BUILD_LOG.md` if you complete or start
   a tracked phase.
5. Significant architectural decisions should be recorded as a new ADR under
   `docs/adr/` (copy the template in `docs/adr/0000-template.md`).

## Code style

- Python: type-hinted, formatted/linted with `ruff`, tested with `pytest`.
- TypeScript: strict mode, formatted/linted with the frontend's ESLint config.
- Terraform/Ansible: idempotent — re-running provisioning must converge, not
  duplicate resources.
- No filler comments. Comment only non-obvious *why*, never restate *what*
  the code does.

## Reporting a security issue in the platform code

See the "Reporting a platform vulnerability" section of
[SECURITY.md](SECURITY.md). Do not open a public issue for platform
vulnerabilities.
