# EADADL — Enterprise Active Directory Attack & Detection Lab

[![CI](https://img.shields.io/badge/CI-not_yet_running-lightgrey)](/.github/workflows)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-early_build-orange)](ROADMAP.md)

A fully isolated, reproducible, **purple-team** laboratory plus a platform
layer that provisions a vulnerable Active Directory environment, orchestrates
attack scenarios against it, ships the resulting telemetry to a SIEM,
validates detections against that telemetry, and reports MITRE ATT&CK
coverage through a web UI.

This is a build-in-progress. **[ROADMAP.md](ROADMAP.md)** and
**[BUILD_LOG.md](BUILD_LOG.md)** are the source of truth for what is actually
done versus planned — this README describes the target architecture, not a
finished product.

## ⚠️ Authorized use only

This repository provisions a **deliberately vulnerable** Active Directory
environment and executes **real offensive security tooling** (NetExec,
Impacket, BloodHound/SharpHound, PowerView, Atomic Red Team, Caldera) against
it. It is built for defenders to practice detection engineering and for red
teamers to practice technique execution in a legal, contained setting.

- Only ever run this against infrastructure you own or are explicitly
  authorized to test.
- The attack engine refuses to target anything outside
  [`inventory/lab-scope.yaml`](inventory/lab-scope.yaml) — see
  [SECURITY.md](SECURITY.md) for the full list of safety invariants.
- This project does not contain novel exploits or malware. It orchestrates
  established, publicly documented tools and maps every technique to a
  published MITRE ATT&CK ID.

## Why this exists

Most "AD attack lab" projects stop at provisioning a vulnerable domain and
running a checklist of attacks by hand. EADADL treats the *detection engineer's
half of the loop* as equally important: every attack technique exercised here
is expected to ship a corresponding [Sigma](https://github.com/SigmaHQ/sigma)
detection rule, tested against the telemetry that technique actually
generates, with the resulting attack→detection coverage tracked and rendered
as an ATT&CK Navigator-style heatmap. It's a purple-team loop, not a red-team
demo.

## Architecture

```mermaid
flowchart TB
    subgraph Lab["Isolated Lab Network (Azure vnet / no internet route)"]
        DC["Domain Controller\n(Windows Server)"]
        MEM["Member Server(s)"]
        WKS["Workstation"]
        ATT["Attacker Box\n(Kali-based)"]
        SIEM["SIEM Host\n(Elastic/Wazuh)"]
        DC <--> MEM
        DC <--> WKS
        ATT -.attacks.-> DC
        ATT -.attacks.-> MEM
        ATT -.attacks.-> WKS
        DC -- Sysmon/WEF --> SIEM
        MEM -- Sysmon/WEF --> SIEM
        WKS -- Sysmon/WEF --> SIEM
    end

    subgraph Platform["Platform Layer (Docker Compose, outside the lab vnet)"]
        API["FastAPI backend\n(runner, history, coverage API, RBAC)"]
        DB[("PostgreSQL")]
        UI["React/Next frontend\n(dashboard, Navigator heatmap, reports)"]
        API <--> DB
        UI <--> API
    end

    Operator(("Operator")) --> UI
    API -- reads --> Scope["inventory/lab-scope.yaml\n(scope guard)"]
    API -- orchestrates --> ATT
    API -- queries --> SIEM
    Detections["detections/ (Sigma + tests)"] -- validated against --> SIEM
```

## Repository layout

```
eadadl/
├── inventory/     # lab-scope.yaml — the ONLY authorized attack targets
├── infra/         # Terraform — the AD environment as code (Azure)
├── config/        # Ansible roles: DC, members, workstation, attacker, SIEM
├── telemetry/     # Sysmon config, WEF/forwarding, SIEM shipping
├── attack/        # scenario engine: atomic techniques + chains, ATT&CK-tagged
├── detections/    # Sigma rules + tests, ATT&CK mapping, detection-as-code
├── platform/
│   ├── backend/   # FastAPI + PostgreSQL: runner, run history, coverage API
│   └── frontend/  # React/Next + Tailwind: dashboard, Navigator heatmap
├── ir/            # DFIR playbooks, hunting notebooks, response automation
├── docs/          # architecture notes, ADRs, runbooks
└── .github/workflows/  # CI: lint, test, detection validation, IaC checks
```

## Deployment target

`DEPLOY_TARGET=azure` (see [`docs/adr/0001-deploy-target.md`](docs/adr/0001-deploy-target.md)
for why). This Mac is Apple Silicon (arm64); VirtualBox has no reliable
Windows-guest support on arm64 hosts, and Microsoft does not publish ARM64
Windows Server media through normal public channels, so a genuine local
Windows Server lab isn't practical here. Terraform provisions an isolated
resource group and vnet in Azure instead — real Windows Server VMs, native
speed, easy teardown, at the cost of requiring Azure credentials and
incurring cloud spend while the lab is up.

### Prerequisites

Install via Homebrew (this account currently lacks the sudo access needed to
install Homebrew itself — run these as an admin, or ask an admin to run them
once):

```bash
brew install terraform packer ansible azure-cli
```

### Quick start (once infra/ is buildable — see ROADMAP.md)

```bash
az login                      # interactive browser auth
cp .env.example .env          # fill in AZURE_SUBSCRIPTION_ID and region
make up                       # terraform apply the lab
make attack SCENARIO=<name>   # run an attack chain against in-scope hosts
make detections-test          # prove the matching Sigma rules fire
make platform                 # serve the dashboard/UI locally
make down                     # full teardown
```

## Documentation

- [SECURITY.md](SECURITY.md) — safety invariants and how to report platform issues
- [docs/vulnerabilities.md](docs/vulnerabilities.md) — every deliberate lab
  misconfiguration, mapped to the ATT&CK technique it enables
- [docs/adr/](docs/adr/) — architecture decision records
- [ROADMAP.md](ROADMAP.md) — honest done/in-progress/not-started status
- [BUILD_LOG.md](BUILD_LOG.md) — session-by-session build history

## License

[MIT](LICENSE)
