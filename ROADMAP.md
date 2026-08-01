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
| CI skeleton (`.github/workflows`) | ⬜ | |
| Homebrew / Packer / QEMU / Ansible installed locally | ⬜ | **blocked**: this account lacks sudo; needs an admin to run the installer |

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
| `generate_bundles.py` (.utm bundle assembly from a manual blank template) | ✅ | plist key names are best-effort, unverified against a real UTM install — see infra/local/README.md |
| One-time blank UTM template creation (arm64 + x86_64) | ⬜ | manual GUI step, not yet performed |
| `scripts/sync_scope.py` (local state + manual IP entry → lab-scope.yaml) | ✅ | written, not yet run (nothing built) |
| AD DS role config + domain promotion (`config/dc/` Ansible) | ⬜ | |
| Member domain join (`config/member/` Ansible) | ⬜ | |
| Synthetic OU/users/groups | ⬜ | |
| Deliberate misconfigs implemented (6 of 8 planned for this footprint — items 5/8 deferred, need `wks01`; see `docs/vulnerabilities.md`) | ⬜ | |
| `make up` (build images + generate bundles) / manual VM boot / `make sync-scope` | ⬜ | requires local Packer/QEMU/Ansible — not run yet |

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

- **No local admin/sudo on this Mac.** Homebrew (and therefore Packer,
  QEMU, Ansible) cannot be installed by this account. Someone with admin
  rights needs to either run the installer or grant this account
  admin/sudo before `make up` can be executed locally. This blocker is
  identical regardless of deploy target — switching from Azure to local
  (ADR 0004) removed the cloud-credential dependency but not this one.
- **Packer/UTM code is unvalidated.** None of `infra/local/packer/*.pkr.hcl`,
  `Autounattend.xml`, the Kali preseed, or `generate_bundles.py`'s plist
  key assumptions have been run against real Packer/QEMU/UTM — there's no
  local install to test against (see blocker above). Treat all of it as a
  careful first draft, not proven-correct. CI's `packer-validate` job
  checks syntax only, not that a build actually succeeds.
- **UTM VM boot is a manual step.** `make up` builds images and generates
  `.utm` bundles but cannot start them — UTM has no verified CLI path for
  that (see `infra/local/README.md`). The operator opens UTM and starts
  the 4 VMs by hand before `make sync-scope` can find their IPs (which
  also requires manually reading each guest's IP into
  `infra/local/discovered-ips.yaml` — see that file's `.example` for why
  this isn't automated either).
