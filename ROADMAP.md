# Roadmap

Honest status tracker. Updated at the end of every work session. Nothing here
is claimed done unless it actually runs from a clean checkout.

Legend: ✅ done · 🚧 in progress · ⬜ not started · 🧪 STUB (present but not functional)

## Phase 0 — Scaffold

| Item | Status | Notes |
|---|---|---|
| Directory layout | ✅ | |
| README, SECURITY, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, CHANGELOG | ✅ | |
| BUILD_LOG.md / ROADMAP.md | ✅ | this session |
| `inventory/lab-scope.yaml` + scope-guard contract | 🚧 | |
| `.env.example` | 🚧 | |
| Makefile skeleton | 🚧 | |
| ADR framework + ADR 0001 (deploy target), ADR 0002 (scope guard) | 🚧 | |
| CI skeleton (`.github/workflows`) | ✅ | |
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
| Wired into `attack/runner.py` | ⬜ | not written yet — see Phase 3 below |

## Phase 2 — Telemetry & detection pipeline

| Item | Status | Notes |
|---|---|---|
| Sysmon config | ⬜ | |
| Windows Event Forwarding | ⬜ | |
| SIEM shipping (Elastic/Wazuh) | ⬜ | |
| Baseline dashboards proving events land | ⬜ | |

## Phase 3 — Attack scenario engine

| Item | Status | Notes |
|---|---|---|
| Atomic technique runner | ⬜ | |
| Attack chains (recon → initial access → cred access → lateral movement → domain dominance) | ⬜ | |
| ATT&CK ID + reference tagging | ⬜ | |
| Result schema + storage | ⬜ | |
| Scope-guard enforcement wired into runner | ⬜ | |

## Phase 4 — Detection library

| Item | Status | Notes |
|---|---|---|
| Sigma rules per exercised technique | ⬜ | |
| Rule tests against real generated telemetry | ⬜ | |
| CI detection validation | ⬜ | |
| Attack→detection coverage matrix | ⬜ | |

## Phase 5 — Platform

| Item | Status | Notes |
|---|---|---|
| FastAPI backend (runner API, run history, coverage API, RBAC) | ⬜ | |
| PostgreSQL schema | ⬜ | |
| React/Next frontend (dashboard, run history, reports) | ⬜ | |
| ATT&CK Navigator coverage heatmap | ⬜ | |
| Dark mode / responsive / accessible | ⬜ | |

## Phase 6 — DFIR / IR

| Item | Status | Notes |
|---|---|---|
| NIST SP 800-61 aligned IR playbooks | ⬜ | |
| Threat-hunting notebooks | ⬜ | |
| SOAR-style response automation hooks | ⬜ | |

## Phase 7 — Polish

| Item | Status | Notes |
|---|---|---|
| Architecture diagrams (mermaid) | 🚧 | one diagram in README so far |
| Full CI/CD | ⬜ | |
| Final honest ROADMAP pass | ⬜ | |

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
