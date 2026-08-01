# Roadmap

Honest status tracker. Updated at the end of every work session. Nothing here
is claimed done unless it actually runs from a clean checkout.

Legend: ✅ done · 🚧 in progress · ⬜ not started · 🧪 STUB (present but not functional)

## At a glance

All 8 phases have real, committed work. What "done" means varies by
layer, and that variance is the whole point of this document — read the
phase tables, not just this summary:

- **Genuinely tested** (real tools, real assertions, run and passing):
  the scope guard, the attack engine's dry-run mode, the detection
  library, the FastAPI backend, the Ansible roles (syntax/lint only, not
  against a live host), the IR response automation. 81 `pytest` tests
  passing (62 at the repo root, 19 in `platform/backend/`), `ruff`/`mypy
  --strict` clean throughout.
- **Written and internally consistent, but unvalidated against real
  infrastructure**: the Packer/UTM local-lab tooling, the telemetry
  config, the Next.js frontend, the Docker Compose files. All blocked on
  the same root cause — see "Known blockers."
- **Not started**: Atomic Red Team/Caldera integration, Wazuh/Splunk SIEM
  backends, detections for misconfigs 6/7, a docs site.

## Phase 0 — Scaffold

| Item | Status | Notes |
|---|---|---|
| Directory layout | ✅ | |
| README, SECURITY, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, CHANGELOG | ✅ | |
| BUILD_LOG.md / ROADMAP.md | ✅ | |
| `inventory/lab-scope.yaml` + scope-guard contract | ✅ | |
| `.env.example` | ✅ | |
| Makefile | ✅ | every target real except the parts genuinely blocked on Packer/QEMU/Docker — see "Known blockers" |
| ADR framework (6 ADRs, 0001–0006: deploy target, scope guard, network isolation ×2, revert-to-local, telemetry) | ✅ | |
| CI (`.github/workflows/ci.yml`, 6 jobs) | ✅ | |
| Homebrew / Packer / QEMU installed locally | ⬜ | **still blocked**: this account lacks sudo, and these need Homebrew specifically |
| Python tooling (pytest, ruff, mypy) + Ansible (ansible-core, ansible-lint) installed locally | ✅ | **unblocked** — all pip-installable at user level (`pip install --user ...`), no sudo needed. This is a real capability unlock: it does NOT solve the Packer/QEMU/UTM blocker (those are Homebrew-only), but it means the Python layer and all of `config/`'s Ansible YAML can be genuinely tested, not just hand-reviewed. See BUILD_LOG.md. |

## Phase 1 — Isolated AD environment (IaC)

`DEPLOY_TARGET` is `local` (UTM/QEMU) as of ADR 0004 — the earlier
`infra/azure/` Terraform (ADR 0001/0003) was removed from the tree; it's
recoverable from git history at commit `67ce0f3` if that path is ever
revisited. Footprint trimmed to 4 hosts (no standalone workstation) — see
ADR 0004.

| Item | Status | Notes |
|---|---|---|
| Packer: Windows Server 2022 template (dc01/mem01, x86_64 TCG-emulated) | ✅ | code written, not build-tested — no local packer/qemu install (see BUILD_LOG.md) |
| Autounattend.xml + bootstrap.ps1 (unattended install, WinRM enable) | ✅ | written, not validated against a real install |
| Packer: Kali ARM64 template (attacker01, native, preseed-driven) | ✅ | written; Kali ARM64 installer preseed is the least-proven part — see BUILD_LOG.md |
| Packer: Ubuntu ARM64 template (siem01, native, cloud-init) | ✅ | written, cloud-init is a well-trodden pattern |
| `generate_bundles.py` (.utm bundle assembly from a manual blank template) | ✅ | `ruff`/`mypy` clean; plist key names are still best-effort, unverified against a real UTM install — see infra/local/README.md |
| One-time blank UTM template creation (arm64 + x86_64) | ⬜ | manual GUI step, not yet performed |
| `scripts/sync_scope.py` (local state + manual IP entry → lab-scope.yaml) | ✅ | `ruff`/`mypy` clean; merge logic covered by 6 passing unit tests (`tests/test_sync_scope.py`) against fixtures — not run against real `infra/local` output (nothing built yet) |
| AD DS role config + domain promotion (`config/dc/` Ansible) | ✅ | `ansible-playbook --syntax-check` passes; `ansible-lint config/` clean at **production** profile — still not run against a real WinRM target |
| Member domain join (`config/member/` Ansible) | ✅ | same validation as above |
| Synthetic OU/users/groups | ✅ | `config/dc/tasks/ou_structure.yml`, `users_and_groups.yml` — syntax/lint-clean, not run-tested |
| Deliberate misconfigs implemented (6 of 8 for this footprint: items 1,2,3,4,6,7; items 5/8 deferred, need `wks01`; see `docs/vulnerabilities.md`) | ✅ | all 6 written across `config/dc/tasks/misconfigs.yml` + `post_join_misconfigs.yml` — syntax/lint-clean, not run-tested |
| `config/site.yml` (dc → member → post-join-misconfigs ordering) + dynamic inventory from `lab-scope.yaml` | ✅ | `ansible-playbook --syntax-check` passes; inventory's `build_inventory()` covered by 6 passing unit tests (`tests/test_lab_scope_inventory.py`) |
| `make up` (build images + generate bundles) / manual VM boot / `make sync-scope` / `ansible-playbook config/site.yml` | ⬜ | requires local Packer/QEMU (still Homebrew-blocked) — not run yet |

### Safety-critical: scope guard (`attack/lib/scope_guard.py`)

The single chokepoint every attack entry point (present and future) must
resolve targets through — see [ADR 0002](docs/adr/0002-scope-guard.md).
Pulled forward and hardened ahead of the rest of Phase 3 because it's the
highest-value, safety-critical piece: everything else in `attack/` is only
as safe as this module.

| Item | Status | Notes |
|---|---|---|
| `ScopeGuard.resolve_target()` — fail-closed resolution (in-scope + provisioned + non-attackable-role + has-IP checks) | ✅ | **actually tested**: 20 passing `pytest` tests (`tests/test_scope_guard.py`), `ruff`/`mypy --strict` clean |
| Negative test coverage: out-of-scope host, unprovisioned host, `attacker`/`siem` roles, missing IP, malformed scope file (bad YAML, missing keys, wrong types, duplicate IDs) | ✅ | 15 of the 20 tests are negative cases — this module's entire job is refusing things |
| No override/bypass parameter | ✅ | asserted directly via `inspect.signature()` in the test suite, not just "we didn't write one" |
| Wired into CI (`python-quality` job) | ✅ | |
| Wired into `attack/runner.py` | ✅ | see Phase 3 below |

## Phase 2 — Telemetry & detection pipeline

Built after Phase 3 (attack engine) this session, per operator priority
order. Every artifact here is pure config — no execution needed to write
it, but also none of it has run against a real host yet, since none
exists (see "Known blockers"). [ADR 0006](docs/adr/0006-telemetry-architecture.md)
records the WEF-collector + single-Winlogbeat-shipper design and, notably,
that Sysmon alone is insufficient for 4 of this lab's misconfigs
(Kerberoasting, AS-REP roasting, ACL abuse, DCSync all require Windows
Security auditing, not Sysmon).

| Item | Status | Notes |
|---|---|---|
| Sysmon config (`telemetry/sysmon/`) | ✅ | well-formed XML confirmed; not deployed/validated against a real Sysmon install |
| Windows Security audit policy + SACLs for Kerberos/DCSync/ACL-abuse detection (`telemetry/windows-audit-policy/`) | ✅ | 3 PowerShell scripts, not run against a real domain; DCSync extended-rights GUIDs flagged for verification |
| Windows Event Forwarding (`telemetry/wef/`) | ✅ | subscription XML well-formed; GPO/wecutil setup documented but manual, not yet in Ansible |
| SIEM shipping — Elastic (`telemetry/winlogbeat/`, `telemetry/elastic/`) | ✅ | winlogbeat.yml + docker-compose + index template, all syntax-validated (YAML/JSON parse); not run against a real Elasticsearch cluster |
| SIEM shipping — Wazuh/Splunk (alternate `SIEM_BACKEND` values) | ⬜ | declared in `.env.example`, no config exists — Elastic only |
| Baseline dashboards proving events land (`telemetry/dashboards/`) | 🚧 | `baseline-queries.md` (raw KQL/DSL, the reliable version) done; `baseline-dashboard.ndjson` is a hand-authored, **not import-tested** Kibana export — see that directory's README for why the queries are the artifact to trust first |
| Wired into `config/dc`/`config/member`/`config/siem` Ansible | ⬜ | everything above is currently a manual/documented procedure, not automated — tracked follow-up |

## Phase 3 — Attack scenario engine

Built ahead of Phase 2 (telemetry) this session, per operator priority: it's
the piece that's fully testable without a live lab, via `--dry-run` mode.
Real (`--live`) execution against actual tooling is unexercised — no lab
exists yet to run it against — but the mode exists and is gated by the
exact same scope guard as dry-run, so there's no separate, less-safe code
path for "real" runs.

| Item | Status | Notes |
|---|---|---|
| Atomic technique runner (`attack/runner.py`) | ✅ | dry-run mode fully tested (11 passing tests); live mode implemented, unexercised |
| Technique registry (`attack/techniques.py`) — 6 techniques | ✅ | Kerberoasting, AS-REP roasting, BloodHound collection, ACL abuse, unconstrained-delegation coercion, DCSync |
| Attack chains (`attack/chains.py`) — 2 chains | ✅ | `credential_harvest` (recon → cred access) and `domain_dominance` (recon → privesc → lateral movement → domain dominance) |
| ATT&CK ID + reference tagging | ✅ | every technique cites a `T####[.###]` ID + `attack.mitre.org` URL; asserted by a test |
| Every target resolved through the Phase-1 scope guard before any tool runs | ✅ | resolved up front for the whole chain, fail-closed, no partial runs — tested, and verified live: `make attack SCENARIO=credential_harvest` against the real (unprovisioned) `inventory/lab-scope.yaml` correctly refuses (`REFUSED: No attackable host with role 'domain_controller'...`) |
| Result schema (`attack/finding.py`: `Finding`) + persistence (`attack/results/*.json`, gitignored) | ✅ | tested |
| `make attack SCENARIO=<name>` | ✅ | dry-run by default; `MODE=live` for real execution (untested, needs a real lab) |
| CI safety smoke-test: runner refuses against the real, unprovisioned scope file | ✅ | `python-quality` CI job |
| Established-tooling orchestration (NetExec, Impacket, BloodHound, bloodyAD) | ✅ | command-building only — dry-run never shells out; live mode does via `subprocess`, unexercised |
| Atomic Red Team / Caldera integration | ⬜ | not attempted — current 6 techniques are hand-modeled against this lab's specific misconfigs rather than pulled from an Atomic Red Team catalog |

## Phase 4 — Detection library

Built with a fixture-based test loop specifically so `make detections-test`
runs green in CI without a live SIEM — same design goal as Phase 3's
dry-run mode. `detections/matcher.py` evaluates real pySigma-parsed
condition trees (not a hand-rolled reimplementation of Sigma's condition
language) against synthetic event dicts.

| Item | Status | Notes |
|---|---|---|
| Sigma rules per exercised technique (`detections/sigma/`) | ✅ | 6 rules, one per `attack/techniques.py` technique — all pass `sigma-cli`'s `sigma check` (0 issues) and pySigma's own parse |
| Rule tests against telemetry fixtures (`detections/fixtures/`, `detections/matcher.py`) | ✅ | every rule proven against ≥1 matching + ≥1 non_matching synthetic event (12 unit tests in `tests/test_matcher.py`, integration tests in `tests/test_detections_runner.py`) — **not** tested against real telemetry, no lab exists yet |
| CI detection validation | ✅ | `.github/workflows/ci.yml`'s `detections-test` job runs `python3 -m detections.test_runner` and uploads `coverage_matrix.json` as a build artifact |
| Attack→detection coverage matrix (`detections/coverage.py`, `detections/coverage_matrix.json`) | ✅ | 6/6 techniques covered (100%), regenerated and committed every `make detections-test` run — feeds the Phase 5 heatmap (not built yet) |
| Detections for misconfigs 6 and 7 | ⬜ | no `attack/techniques.py` technique exercises the GPO edit-rights abuse or SYSVOL credential read yet, so no Sigma rule exists for either — see `docs/vulnerabilities.md`'s Detection column |

## Phase 5 — Platform

The backend is the second fully-tested layer this session (after the
Python/Ansible layers) — FastAPI/SQLAlchemy/pytest are all pip-installable
without admin rights. The frontend needs Node.js, which needs Homebrew,
which needs admin rights this account doesn't have — so it's written but
genuinely unvalidated, flagged accordingly rather than presented with the
same confidence. See `platform/README.md`.

| Item | Status | Notes |
|---|---|---|
| FastAPI backend (runner API, run history, coverage API, RBAC) | ✅ | **19/19 tests passing**, `ruff`/`mypy --strict` clean — `platform/backend/` |
| SQLAlchemy schema (users, scenario_runs, run_findings) | ✅ | SQLite by default, Postgres via `platform/docker-compose.yml`; no Alembic migrations (documented scope decision, see `platform/backend/README.md`) |
| Auth / RBAC (JWT, viewer/operator roles) | ✅ | tested — includes a negative test proving a `viewer` cannot trigger a run (403) |
| `POST /runs` gated by the real scope guard | ✅ | tested against the real, unprovisioned `inventory/lab-scope.yaml` — returns 403, same as `make attack`'s CLI safety smoke test |
| React/Next frontend (dashboard, run history, run detail, coverage heatmap) | 🚧 | written (`platform/frontend/`) — **not validated**: no local Node.js, so no `npm install`/`tsc`/`eslint`/browser render has happened |
| ATT&CK-style coverage heatmap | 🚧 | `src/components/CoverageHeatmap.tsx` reads the real `GET /coverage` endpoint — same "written, unvalidated" caveat as the rest of the frontend |
| Dark mode / responsive / accessible | 🚧 | Tailwind `dark:` classes used throughout; not verified in an actual browser |
| `platform/docker-compose.yml` | 🚧 | written, syntax-checked (YAML parse) — not run, no local Docker |
| CI backend/frontend jobs | ✅ | `.github/workflows/ci.yml`'s `backend` job now runs for real (two-step install — see `platform/backend/README.md`); `frontend` job will be the first real validation of that code whenever this branch is pushed |

## Phase 6 — DFIR / IR

| Item | Status | Notes |
|---|---|---|
| NIST SP 800-61 aligned IR playbooks (`ir/playbooks/`) | ✅ | 5 playbooks (Kerberoasting, AS-REP roasting, ACL abuse, unconstrained delegation, DCSync), each citing its Sigma rule/telemetry/`docs/vulnerabilities.md` item |
| Threat-hunting notebooks (`ir/notebooks/`) | ✅ | 1 notebook, 5 hunts (one per detected technique), built + schema-validated via `nbformat` — **not run** against a real cluster |
| SOAR-style response automation hooks (`ir/automation/`) | ✅ | `responder.py`, 7 passing tests — dry-run only by design (see `ir/automation/README.md` "Design"), reuses the same scope guard as `attack/runner.py` |

## Phase 7 — Polish

| Item | Status | Notes |
|---|---|---|
| Architecture diagrams (mermaid) | ✅ | README.md's high-level host/platform diagram, plus [`docs/architecture.md`](docs/architecture.md)'s telemetry data-flow, `domain_dominance` attack-chain sequence, and purple-team-loop diagrams |
| CI (`.github/workflows/ci.yml`) | ✅ | 6 jobs: `packer-validate`, `ansible-lint` (now installs `config/requirements.yml`'s collections + runs `ansible-playbook --syntax-check`, not just lint, so CI actually reproduces what was verified locally), `python-quality` (+ the attack-CLI safety smoke test), `detections-test` (+ coverage-matrix artifact upload), `backend`, `frontend` |
| Makefile | ✅ | every target does something real; `up`/`platform` correctly refuse to run past `check-tools` given this machine's blockers, rather than pretending to succeed |
| Final honest ROADMAP pass | ✅ | this pass — fixed several stale 🚧/⬜ rows left over from earlier in this session, removed one duplicate row (Phase 3), renumbered/recounted ADRs |
| CONTRIBUTING.md / CODE_OF_CONDUCT.md / CHANGELOG.md | ✅ | CHANGELOG.md updated this pass to summarize the whole session; CONTRIBUTING/CODE_OF_CONDUCT unchanged since Phase 0, still accurate |
| Docs site | ⬜ | not attempted — this repo's Markdown-as-you-browse-GitHub structure was judged sufficient for the project's current size, not a gap being actively tracked |

## Known blockers

- **No local admin/sudo on this Mac — but this is narrower than it first
  looked.** Homebrew itself cannot be installed by this account, which
  blocks **Packer, QEMU, and UTM's underlying tooling specifically** (they
  have no pip/pure-Python install path). It does NOT block Python tooling
  or Ansible: `pytest`, `ruff`, `mypy`, `ansible-core`, and `ansible-lint`
  all installed successfully via `pip install --user` (no sudo needed) —
  see BUILD_LOG.md. So: `make up` (which needs Packer/QEMU) still can't run
  locally; `make lint`/`make test` (Python + Ansible-lint) now can and do.
  Someone with admin rights still needs to run the Homebrew installer, or
  grant this account admin/sudo, before a real VM can be built.
- **Packer/UTM code is unvalidated against real Packer/QEMU/UTM.** None of
  `infra/local/packer/*.pkr.hcl`, `Autounattend.xml`, the Kali preseed, or
  `generate_bundles.py`'s plist key assumptions have been build-tested —
  see the blocker above. `packer fmt`/`packer validate` specifically (as
  opposed to Python/Ansible) still can't run locally; CI's
  `packer-validate` job is the only current validation, and it checks
  syntax only, not that a build actually succeeds.
- **UTM VM boot is a manual step.** `make up` builds images and generates
  `.utm` bundles but cannot start them — UTM has no verified CLI path for
  that (see `infra/local/README.md`). The operator opens UTM and starts
  the 4 VMs by hand before `make sync-scope` can find their IPs (which
  also requires manually reading each guest's IP into
  `infra/local/discovered-ips.yaml` — see that file's `.example` for why
  this isn't automated either).
- **Ansible roles are syntax/lint-clean but unvalidated against a real
  target.** `ansible-playbook --syntax-check` passes and `ansible-lint
  config/` is clean at the production profile (both now actually run, not
  assumed — see above), but there is still no real WinRM-reachable Windows
  host to execute against. The misconfig-4 ACL-grant PowerShell and the
  Kerberoasting/AS-REP-roasting setup are the parts most worth re-checking
  by hand once a target exists, since they're the core of what makes the
  lab useful and PowerShell-inside-`win_shell` is invisible to
  `ansible-lint`.
- **Node.js and Docker are blocked the same way Packer/QEMU are.** Both
  need Homebrew, which needs admin rights this account doesn't have. This
  is why `platform/backend/` (pure Python) could be fully tested this
  session while `platform/frontend/` (Node.js) and
  `platform/docker-compose.yml` (Docker) could not — not a difference in
  effort, a difference in what's pip-installable versus what needs a
  system package manager.
- **No CI has ever actually run.** This repo has no git remote configured
  (`git remote -v` is empty) — every "CI does X" claim throughout this
  project (and there are many, across `ROADMAP.md` and `BUILD_LOG.md`) is
  a claim about what `.github/workflows/ci.yml` *would* do, verified by
  reproducing the same commands locally, not by an observed GitHub
  Actions run. Push this branch to a real remote for the first genuine
  end-to-end validation of the CI configuration itself.
