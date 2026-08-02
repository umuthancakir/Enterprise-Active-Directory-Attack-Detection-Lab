# Roadmap

Honest status tracker. Updated at the end of every work session. Nothing here
is claimed done unless it actually runs from a clean checkout.

Legend: ✅ done · 🚧 in progress · ⬜ not started · 🧪 STUB (present but not functional)

## At a glance

**Session 4 update: QEMU is genuinely installed (source build, no
Homebrew — see "Known blockers"), and the local lab is no longer purely
theoretical.** `siem01` (Ubuntu, native arm64) is **built, booted, and
SSH-reachable for real** — the first host this project has ever actually
run. `telemetry/elastic/docker-compose.yml` is deployed on it for real
(Docker installed fresh via `apt`, a normal guest-side operation) and all
8 Sigma detections are verified against that real, running,
security-enabled Elasticsearch cluster, not a mock. `dc01` (Windows
Server) got much further than ever before — a real, complete Windows
install, `AutoLogon` working, a genuine desktop reached — with a real,
diagnosed WinRM fix applied (see below); as of this entry a rebuild with
that fix is still running. `attacker01` (Kali) remains blocked on an
unresolved Debian-installer locale prompt. See BUILD_LOG.md session 4
for the full account — five real, independent bugs found and fixed
getting `siem01` this far, all invisible to any validation short of an
actual build.

All 8 phases have real, committed work. What "done" means varies by
layer, and that variance is the whole point of this document — read the
phase tables, not just this summary:

- **Genuinely tested against a live target** (new this session): `siem01`
  build + boot + provisioning (Packer, real QEMU), the real
  `telemetry/elastic/docker-compose.yml` deployment and its 8/8 Sigma
  detections against a real Elasticsearch cluster.
- **Genuinely tested** (real tools, real assertions, run and passing):
  the scope guard, the attack engine's dry-run mode (including the
  Atomic Red Team schema integration), the detection library (8/8
  coverage, both the abstract matcher and — new — real Elasticsearch
  Lucene queries), the FastAPI backend, the Ansible roles (syntax/lint
  only, not yet against a live host — `dc01`/`mem01` aren't reachable
  yet), the IR response automation. 79 `pytest` tests passing at the
  repo root (up from 72), `ruff`/`mypy --strict` clean throughout.
- **Written and internally consistent, but unvalidated against real
  infrastructure**: `dc01`/`mem01` (Windows, in progress — see above),
  `attacker01` (blocked), the Next.js frontend, the platform Docker
  Compose file (still blocked on Docker on the *host*, distinct from
  Docker on the *guest*, which now works fine — see "Known blockers").
- **Not started**: Caldera integration, Wazuh/Splunk SIEM backends
  (the latter deliberately deferred until Elastic is validated end-to-end
  against a live lab — Elastic itself now is, see above), a docs site.

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
| Packer: Windows Server 2022 template (dc01/mem01, x86_64 TCG-emulated) | 🚧 | **build-tested for real** (session 4) — a full install completed, `AutoLogon` worked, a genuine desktop was reached; WinRM never came up because `D:\bootstrap.ps1` never ran (a real, diagnosed macOS-only Packer bug — see BUILD_LOG.md), fixed, rebuild in progress as of this entry |
| Autounattend.xml + bootstrap.ps1 (unattended install, WinRM enable) | 🚧 | Autounattend.xml itself validated for real (MBR partition fix, `AutoLogon` both confirmed working on a real install); bootstrap.ps1's delivery mechanism was broken (see above) and is fixed but not yet confirmed to actually run end-to-end |
| Packer: Kali ARM64 template (attacker01, native, preseed-driven) | 🚧 | **build-tested for real** — reaches Kali's real GRUB-based installer (three real bugs found and fixed: missing GPU/input devices, wrong EFI boot mechanism, missing `http_directory`) but blocked on an interactive "Select a language" dialog that survives Debian's own documented kernel-cmdline suppression params — see "Known blockers" |
| Packer: Ubuntu ARM64 template (siem01, native, cloud-init) | ✅ | **built, booted, and SSH-reachable for real** — `infra/local/build/images/siem01/siem01.qcow2` is a genuine, working artifact. Two real bugs found and fixed beyond the obvious: Packer's cd_files ISO generation is broken on macOS (upstream bug, worked around with a custom pycdlib-based ISO builder) and `qemu-guest-agent.service` needs an explicit virtio-serial device nothing provides by default. See BUILD_LOG.md session 4 for the full account. |
| `generate_bundles.py` (.utm bundle assembly from a manual blank template) | ✅ | `ruff`/`mypy` clean; plist key names are still best-effort, unverified against a real UTM install — see infra/local/README.md. **Not the path used to validate builds this session** — see "Known blockers" for why direct QEMU invocation was used instead |
| One-time blank UTM template creation (arm64 + x86_64) | ⬜ | manual GUI step, not yet performed |
| `scripts/sync_scope.py` (local state + manual IP entry → lab-scope.yaml) | ✅ | **run for real** against genuine `infra/local/state.json` + `discovered-ips.yaml` (hand-written this session, not `generate_bundles.py`'s output — see "Known blockers") — `inventory/lab-scope.yaml` correctly shows `siem01` as `provisioned: true`. 8 passing unit tests (`tests/test_sync_scope.py`, +2 for the new `ssh_port` field) |
| AD DS role config + domain promotion (`config/dc/` Ansible) | ✅ | `ansible-playbook --syntax-check` passes; `ansible-lint config/` clean at **production** profile — still not run against a real WinRM target (`dc01` isn't reachable yet) |
| Member domain join (`config/member/` Ansible) | ✅ | same validation as above |
| Synthetic OU/users/groups | ✅ | `config/dc/tasks/ou_structure.yml`, `users_and_groups.yml` — syntax/lint-clean, not run-tested |
| Deliberate misconfigs implemented (6 of 8 for this footprint: items 1,2,3,4,6,7; items 5/8 deferred, need `wks01`; see `docs/vulnerabilities.md`) | ✅ | all 6 written across `config/dc/tasks/misconfigs.yml` + `post_join_misconfigs.yml` — syntax/lint-clean, not run-tested |
| `config/site.yml` (dc → member → post-join-misconfigs ordering) + dynamic inventory from `lab-scope.yaml` | 🚧 | `ansible-playbook --syntax-check` passes; inventory's `build_inventory()` covered by 8 passing unit tests. **Run for real** against the current inventory (session 4) — correctly matched 0 hosts, since `site.yml` only targets `domain_controller`/`member_server` and only `siem01` is provisioned so far; genuinely meaningful validation is still gated on `dc01` |
| `make up` (build images + generate bundles) / manual VM boot / `make sync-scope` / `ansible-playbook config/site.yml` | 🚧 | Packer builds now genuinely run (see above); manual UTM boot was substituted with direct `qemu-system-{aarch64,x86_64}` invocation this session (see "Known blockers" for why); `make sync-scope` and `ansible-playbook` both run for real against the result |

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
| Windows Security audit policy + SACLs for Kerberos/DCSync/ACL-abuse/GPO/SYSVOL detection (`telemetry/windows-audit-policy/`) | ✅ | 5 PowerShell scripts (added `configure-gpo-sacl.ps1` + `configure-sysvol-file-sacl.ps1` to close the misconfig 6/7 detection gap — see Phase 4), not run against a real domain; DCSync extended-rights GUIDs flagged for verification |
| Windows Event Forwarding (`telemetry/wef/`) | ✅ | subscription XML well-formed; GPO/wecutil setup documented but manual, not yet in Ansible |
| SIEM shipping — Elastic (`telemetry/winlogbeat/`, `telemetry/elastic/`) | 🚧 | **`docker-compose.yml` + `index-template.json` run for real** (session 4) — deployed onto the real `siem01` host, `xpack.security` enabled, index template applied via a real API call, all 8 Sigma detections verified against it (see Phase 4). `winlogbeat.yml` (the `dc01`-side shipper) is still unvalidated — no reachable Windows host with real Security events yet |
| SIEM shipping — Wazuh/Splunk (alternate `SIEM_BACKEND` values) | ⬜ | **deliberately deferred** — declared in `.env.example`, no config exists. Per operator instruction, held until at least one SIEM backend (Elastic) is validated end-to-end against a live lab, rather than building a second unvalidated backend in parallel |
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
| Technique registry (`attack/techniques.py`) — 8 techniques | ✅ | Kerberoasting, AS-REP roasting, BloodHound collection, ACL abuse, unconstrained-delegation coercion, DCSync, GPO edit-rights abuse, SYSVOL credential read — one per implementable misconfig (items 1,2,3,4,6,7) |
| Attack chains (`attack/chains.py`) — 3 chains | ✅ | `credential_harvest` (recon → cred access), `domain_dominance` (recon → privesc → lateral movement → domain dominance), `gpo_and_sysvol_abuse` (recon → GPO persistence abuse → credential exposure, independent of the other two) |
| ATT&CK ID + reference tagging | ✅ | every technique cites a `T####[.###]` ID + `attack.mitre.org` URL; asserted by a test |
| Every target resolved through the Phase-1 scope guard before any tool runs | ✅ | resolved up front for the whole chain, fail-closed, no partial runs — tested, and verified live: `make attack SCENARIO=credential_harvest` against the real (unprovisioned) `inventory/lab-scope.yaml` correctly refuses (`REFUSED: No attackable host with role 'domain_controller'...`) |
| Result schema (`attack/finding.py`: `Finding`) + persistence (`attack/results/*.json`, gitignored) | ✅ | tested |
| `make attack SCENARIO=<name>` | ✅ | dry-run by default; `MODE=live` for real execution (untested, needs a real lab) |
| CI safety smoke-test: runner refuses against the real, unprovisioned scope file | ✅ | `python-quality` CI job |
| Established-tooling orchestration (NetExec, Impacket, BloodHound, bloodyAD) | ✅ | command-building only — dry-run never shells out; live mode does via `subprocess`, unexercised |
| Atomic Red Team integration (`attack/integrations/`) | 🚧 | real parser for ART's public YAML schema + a small hand-written local catalog (3 recon techniques: T1087.002, T1069.002, T1018), dry-run only, same scope guard — 10 passing tests. **Not** a vendored copy of the upstream project (thousands of files, independent license) — see `attack/integrations/README.md` for what would be needed to go further |
| Caldera integration | ⬜ | not attempted |

## Phase 4 — Detection library

Built with a fixture-based test loop specifically so `make detections-test`
runs green in CI without a live SIEM — same design goal as Phase 3's
dry-run mode. `detections/matcher.py` evaluates real pySigma-parsed
condition trees (not a hand-rolled reimplementation of Sigma's condition
language) against synthetic event dicts.

| Item | Status | Notes |
|---|---|---|
| Sigma rules per exercised technique (`detections/sigma/`) | ✅ | 8 rules, one per `attack/techniques.py` technique — all pass `sigma-cli`'s `sigma check` (0 issues) and pySigma's own parse |
| Rule tests against telemetry fixtures (`detections/fixtures/`, `detections/matcher.py`) | ✅ | every rule proven against ≥1 matching + ≥1 non_matching synthetic event, `tests/test_matcher.py` + `tests/test_detections_runner.py` — **not** tested against real telemetry, no lab exists yet |
| CI detection validation | ✅ | `.github/workflows/ci.yml`'s `detections-test` job runs `python3 -m detections.test_runner` and uploads `coverage_matrix.json` as a build artifact |
| Attack→detection coverage matrix (`detections/coverage.py`, `detections/coverage_matrix.json`) | ✅ | **8/8 techniques covered (100%)**, regenerated and committed every `make detections-test` run — feeds the Phase 5 heatmap |
| Detections for misconfigs 6 and 7 | ✅ | `gpo_edit_abuse` (T1484.001, requires `telemetry/windows-audit-policy/configure-gpo-sacl.ps1`) and `sysvol_credential_read` (T1552.001, requires `configure-sysvol-file-sacl.ps1` — a filesystem SACL, not an AD one) — closes the coverage-matrix gap flagged in the previous pass |
| Elasticsearch backend (`detections/elastic_backend.py`, `detections/elastic_integration_check.py`) | ✅ | **new this session, genuinely tested against a real cluster.** `elastic_backend.py` converts every rule to a real Lucene query via pySigma's own ES backend (deterministic, in the default CI suite — `tests/test_elastic_backend.py`). `elastic_integration_check.py` is the live-cluster counterpart (deliberately kept out of CI, same reasoning as `sigma-cli`) — run against a real, security-enabled `telemetry/elastic/docker-compose.yml` deployed on `siem01`: **8/8 techniques verified**, every matching fixture hit and every non_matching fixture correctly didn't. Found and fixed one real bug along the way: ES's default dynamic mapping analyzes string fields as full-text, silently breaking wildcard queries on fields like `ObjectName` — fixed by mapping fixture fields `keyword`, the same assumption the real winlogbeat index template already makes |

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
| NIST SP 800-61 aligned IR playbooks (`ir/playbooks/`) | ✅ | 7 playbooks (Kerberoasting, AS-REP roasting, ACL abuse, unconstrained delegation, DCSync, GPO edit-rights abuse, SYSVOL credential exposure), each citing its Sigma rule/telemetry/`docs/vulnerabilities.md` item |
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

- **✅ RESOLVED: no CI had ever actually run.** As of `main`@`85825bf`
  (2026-08-01, session 3), this repo is on a real GitHub remote and CI has
  run for real, twice. **Run 1 (`09bbcfb`) found 2 real failures** on a
  clean runner that local reproduction had never caught: `packer fmt`
  drift (the 3 `.pkr.hcl` files had never been formatted, since Packer
  wasn't installed locally at the time) and a backend `mypy` failure
  (`types-python-jose` had been installed ad-hoc on the dev machine during
  troubleshooting but never added to `platform/backend/pyproject.toml`).
  Investigating the Packer failure surfaced two more real bugs: CI's
  `packer-validate` job ran from the wrong working directory (the
  templates' relative paths are relative to the repo root, matching how
  `build.sh`/`build-linux.sh` actually invoke packer, not
  `infra/local/packer/`), and the `windows-update` provisioner needs a
  plugin declaration it didn't have. **Run 2 (`85825bf`) is fully green —
  all 6 jobs pass.** See BUILD_LOG.md session 3 for the full account,
  including a self-caught error: the placeholder SHA-256 checksum used
  for `packer validate` was miscounted by hand (wrong number of zeros) —
  twice — while fixing this, before being generated and length-checked
  programmatically instead of hand-typed.
- **Revised finding: this account has less-restricted permissions than
  earlier sessions assumed — the real constraint is no interactive TTY,
  not "no admin rights."** `id` shows this account IS a member of the
  `admin` group. `sudo`/Homebrew installation still can't run here because
  they require an interactive password prompt this non-interactive shell
  environment can't provide (`git`'s HTTPS auth failed the same way:
  `could not read Username... Device not configured`) — not because the
  account lacks the underlying privilege. This distinction mattered in
  practice: **Packer and the GitHub CLI (`gh`) are both now installed and
  working**, via their official standalone release binaries downloaded
  directly from `releases.hashicorp.com`/GitHub releases into
  `~/.local/bin` — no Homebrew, no sudo, no interactive prompt needed.
  `gh auth login`'s device-code flow (a *browser-side* interactive step
  the operator completes, not a local TTY prompt) was how git push
  authentication got resolved too.
- **✅ RESOLVED (session 4): QEMU is genuinely installed.** Neither
  Homebrew nor MacPorts install QEMU without the same interactive-TTY
  sudo prompt this environment can't provide (MacPorts' own installer
  needs the same kind of privileged step, GUI or not), and QEMU
  publishes no standalone macOS binaries the way Packer/gh do. Built
  from source instead, entirely without sudo: conda-forge (via an
  Anaconda install already present on this machine) has every build
  dependency QEMU needs — `pixman`, `glib`, `pkg-config`, `ninja`,
  `meson`, `libslirp` — for osx-arm64, installed into a dedicated conda
  env. QEMU 9.2.0 built and ran, but crashed under `-cpu host` on this
  machine's Apple M4 Pro chip (`Property 'host-arm-cpu.sme' not found` —
  a real HVF/SME feature-detection gap for CPU generations newer than
  that release); QEMU **11.0.3** (current stable) doesn't hit this bug.
  Both `qemu-system-x86_64 --version` and `qemu-system-aarch64 --version`
  exit 0, and — more importantly — both accelerators the project's
  templates actually use (`-M pc -accel tcg`, `-M virt -accel hvf -cpu
  host`) were verified with real boot tests, not just version checks.
- **UTM's embedded QEMU can't be reused directly — genuinely checked, not
  assumed.** UTM.app (already installed) bundles its own compiled QEMU at
  `Contents/Frameworks/qemu-{arch}-softmmu.framework/`, but `otool -hv`
  shows `filetype DYLIB`: UTM links QEMU in-process as a library, not a
  CLI binary Packer's builder could shell out to (confirmed by trying to
  exec one directly — `exec format error`).
- **UTM GUI boot was substituted with direct QEMU invocation for this
  session's validation — a real, working host, just not through UTM.**
  UTM has no scriptable boot path (see `infra/local/README.md`), and
  nothing about that changed this session — an operator still needs to
  open UTM and click start for the *intended* deploy path. What changed:
  since the built `.qcow2` artifacts are real and QEMU is now installed,
  `siem01` was booted directly via `qemu-system-aarch64` (same
  accelerator/machine-type the `.pkr.hcl` templates use) to get a
  genuine, reachable host for validation this session, reachable at
  `127.0.0.1` + a host-side forwarded port (`infra/local/state.json`'s
  `ssh_port` field, plumbed through `scripts/sync_scope.py` into
  `config/inventory/lab_scope_inventory.py`'s `ansible_port`) rather than
  a real routable UTM host-only IP. `infra/local/generate_bundles.py`
  (the actual `.utm`-bundle path) is unchanged and still unvalidated.
- **Packer's `cd_files`/`cd_label` mechanism is broken on macOS — a real,
  known upstream bug, not something specific to this project's
  templates.** Packer's SDK unconditionally builds `cd_files` ISOs via
  `hdiutil makehybrid -hfs -joliet -iso ...`
  ([packer-plugin-qemu#133](https://github.com/hashicorp/packer-plugin-qemu/issues/133)),
  which wraps the ISO9660 filesystem in an HFS+ hybrid layer that both
  Linux's cloud-init NoCloud datasource and Windows' runtime CDFS driver
  fail to read correctly (each in a different way — see BUILD_LOG.md
  session 4 for both). `xorriso`/`mkisofs` avoid the bug but have no
  non-Homebrew install path here either. Fixed for both `siem01` and
  `dc01`/`mem01` with a small pycdlib-based ISO builder
  (`infra/local/iso_builder.py`) that bypasses `cd_files` entirely.
- **Ansible roles are syntax/lint-clean and CI-verified, and `siem01` is
  now a real reachable target — but `config/site.yml` doesn't cover it.**
  `ansible-playbook --syntax-check` passes and `ansible-lint config/` is
  clean at the production profile, verified in CI on every push. Run for
  real against the current inventory (session 4): 0 hosts matched, since
  `site.yml`'s three plays only target `domain_controller`/
  `member_server` and only `siem01` (role `siem`) is provisioned so far.
  Genuinely meaningful Ansible validation is still gated on `dc01`
  becoming WinRM-reachable. The misconfig-4 ACL-grant PowerShell and the
  Kerberoasting/AS-REP-roasting setup remain the parts most worth
  re-checking by hand once that happens, since PowerShell-inside-
  `win_shell` is invisible to `ansible-lint`.
- **Node.js and Docker remain unavailable on the *host* — same root cause
  as QEMU used to be, not Packer/gh's. Docker on a *guest* is a different
  story and now works fine.** `platform/frontend/`'s `npm install`/
  `eslint`/`tsc`/`npm test` and `platform/docker-compose.yml` (which runs
  outside the lab network, on the host) have still never run locally —
  but both are verified in CI. Separately, `siem01` (a normal Ubuntu
  guest, unrelated to what's installable on the macOS host) got Docker
  via a plain `apt-get install docker.io` with no issues at all, and
  `telemetry/elastic/docker-compose.yml` runs on it for real — see Phase
  2/4 above.
- **`attacker01` (Kali) is blocked on an interactive language-selection
  prompt that survives Debian's own documented suppression mechanism.**
  Three real bugs were found and fixed getting this far (missing GPU/USB
  input devices on QEMU's aarch64 `virt` machine, the wrong EFI boot
  mechanism, an accidentally-dropped `http_directory` — see BUILD_LOG.md
  session 4), but the installer still stops at an interactive "[!!]
  Select a language" dialog before `netcfg` brings up networking (i.e.
  before the network preseed can ever be fetched to answer it). Tried
  Debian's documented kernel-cmdline fix for exactly this case
  (`debian-installer/locale=en_US.UTF-8
  keyboard-configuration/xkb-keymap=us`) twice, including the simplified
  minimal-recipe version — confirmed via a real rebuild that the same
  dialog still appears regardless. Next untried step: Kali's
  `simple-cdd/profiles=kali` + on-disc `preseed/file=` layer (visible in
  the boot line) may be interposing its own earlier prompt ahead of
  stock Debian-installer's.
- **`dc01`/`mem01` (Windows) are close but not confirmed yet.** A build
  got further than ever before this session — full install, `AutoLogon`,
  a real desktop — before being blocked on WinRM (root-caused: the
  `cd_files` bug above meant `bootstrap.ps1` never ran; confirmed by
  probing the WinRM endpoint directly and reading its
  `WWW-Authenticate: Negotiate`-only header, not by guessing from a
  timeout). A rebuild with the real fix (the same pycdlib-based ISO
  builder, extended to replicate the main disk + install ISO drives
  alongside the custom seed since Packer's `qemuargs` override
  suppresses *all* auto-generated drives once any custom one is added —
  see BUILD_LOG.md) was still running as of this entry. `mem01` hasn't
  been attempted at all — same template, once `dc01` is confirmed.
