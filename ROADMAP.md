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
| Homebrew / Terraform / Ansible / Packer / Azure CLI installed locally | ⬜ | **blocked**: this account lacks sudo; needs an admin to run the installer |

## Phase 1 — Isolated AD environment (IaC)

| Item | Status | Notes |
|---|---|---|
| Terraform azurerm: resource group, vnet, NSGs (no internet route) | ⬜ | code only, no `apply`, per operator instruction |
| Domain Controller VM + AD DS role config | ⬜ | |
| Member server(s) | ⬜ | |
| Workstation | ⬜ | |
| Attacker box (Kali-based) | ⬜ | |
| SIEM host | ⬜ | |
| Synthetic OU/users/groups | ⬜ | |
| Deliberate misconfigs documented in `docs/vulnerabilities.md` | ⬜ | |
| `make up` / `make down` actually provision/destroy | ⬜ | requires Azure credentials — not run yet |

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

- **No local admin/sudo on this Mac.** Homebrew (and therefore Terraform,
  Ansible, Packer, Azure CLI) cannot be installed by this account. Someone
  with admin rights needs to either run the installer or grant this account
  admin/sudo before `make up` can be executed locally.
- **No Azure credentials provided yet.** Per operator instruction, `infra/`
  is being scaffolded as code without running `az login` or `terraform
  apply`. Live provisioning is blocked on the operator providing a
  subscription ID/region and completing `az login` when ready.
