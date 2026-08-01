# Build Log

Session-by-session record of what was actually done. Radical honesty: this
log records real actions taken, not intended future work (that's
[ROADMAP.md](ROADMAP.md)).

## 2026-08-01 — Session 1: Phase 0 scaffold

**Environment discovered:**

- Host: Apple Silicon (arm64) macOS, empty non-git directory.
- Installed: VirtualBox (`VBoxManage`), UTM.app. Not installed: Vagrant,
  Terraform, Ansible, Packer, Docker, Homebrew, Azure CLI.
- This account does **not** have sudo/admin rights on the machine — the
  Homebrew installer failed with "Need sudo access... needs to be an
  Administrator". Tooling install is deferred until an admin runs it; this
  does not block scaffolding code, only running `terraform apply` /
  `az login` locally later.

**Decisions made (with operator):**

- `DEPLOY_TARGET=azure` — chosen over local UTM/QEMU emulation or native
  ARM64 Windows Server, because VirtualBox doesn't reliably support Windows
  guests on arm64 hosts and Microsoft doesn't publish ARM64 Windows Server
  media through normal public channels. See
  [`docs/adr/0001-deploy-target.md`](docs/adr/0001-deploy-target.md).
- Azure auth: interactive `az login`, not a stored service-principal secret,
  for this single-operator stage.
- Operator asked to skip live Azure provisioning for now: scaffold all
  `infra/` Terraform and document the exact subscription/region/auth steps
  needed, but do not run `terraform apply` or require credentials yet.

**Work done:**

- git repo initialized (`main` branch).
- Directory scaffold created: `inventory/`, `infra/azure/`, `config/{dc,
  member,workstation,attacker,siem}/`, `telemetry/{sysmon,wef}/`,
  `attack/{techniques,chains,lib}/`, `detections/{sigma,tests}/`,
  `platform/{backend,frontend}/`, `ir/{playbooks,notebooks,automation}/`,
  `docs/adr/`, `.github/workflows/`.
- Governance docs written: `README.md`, `SECURITY.md`, `LICENSE` (MIT),
  `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`.
- `ROADMAP.md` and this `BUILD_LOG.md` created.

**Status:** Phase 0 in progress — scope guard, `.env.example`, Makefile, ADRs,
and CI skeleton not yet committed (in progress this same session, see
ROADMAP.md for current state).

**Not done / explicitly deferred:**

- No infrastructure has been provisioned. No Azure resources exist yet.
- No tests have been run (none exist yet).
- Homebrew/Terraform/Ansible/Packer/Azure CLI are not installed on this
  machine; an admin needs to run the installer before `make up` can actually
  execute against Azure.

## 2026-08-01 — Session 1 continued: Phase 1 Terraform scaffold

**Work done (per operator instruction: code only, no `terraform apply`, no
credentials required yet):**

- ADR 0003 written: defines the Azure network isolation model — no lab VM
  gets a public IP or an outbound route to the internet; Azure Bastion is
  the sole (inbound-only) management path; the mandatory Azure platform
  channel (168.63.129.16) is explicitly scoped out of the "no internet"
  invariant and documented as such so it isn't mistaken for a gap later.
- `infra/azure/` written: `versions.tf` (provider pins), `variables.tf`,
  `main.tf` (resource group + generated admin credential), `network.tf`
  (vnet, lab subnet, AzureBastionSubnet, NSG denying inbound/outbound
  Internet), `bastion.tf` (the only public IP in the deployment, locked to
  `var.operator_source_ips`), `dc.tf`/`member.tf`/`workstation.tf`
  (Windows Server 2022 / Windows 11 VMs), `attacker.tf` (Kali Linux
  marketplace image, SSH-key auth), `siem.tf` (Ubuntu 22.04, SSH-key auth),
  `outputs.tf`, `terraform.tfvars.example`.
- Linux hosts (attacker, SIEM) use `tls_private_key`-generated SSH keys
  rather than password auth — tightened this from an initial password-auth
  draft to match the project's least-privilege/secure-by-design standard.
- `scripts/sync_scope.py` written: reads `terraform output -json` and
  writes host IPs + provisioned state into `inventory/lab-scope.yaml`, the
  mechanism ADR 0002 depends on to keep the scope guard's allow-list from
  drifting from what's actually deployed.
- `docs/vulnerabilities.md` written as a **design document** — 8 planned
  deliberate misconfigurations mapped to ATT&CK technique IDs with
  reference links. None are implemented yet; that happens via the
  `config/dc/` and `config/member/` Ansible roles, which do not exist yet.

**Verification performed:** brace-balance check across all `.tf` files
(sanity only). **Not verified:** `terraform validate`/`terraform fmt` could
not be run — Terraform is not installed locally (see "Known blockers" in
ROADMAP.md). CI's `terraform-validate` job will be the first real validation
once this is pushed to GitHub.

**Not done / explicitly deferred:**

- No `terraform apply` has been run; no Azure resources exist.
- Domain promotion, OU/user/group creation, and all 8 deliberate
  misconfigurations in `docs/vulnerabilities.md` are unimplemented —
  `config/dc/`, `config/member/`, `config/workstation/` Ansible roles don't
  exist yet.
- NSG intra-lab rule (`allow-intra-lab` in `network.tf`) is a full mesh
  within the subnet rather than a scoped port matrix (AD/Kerberos/SMB/WinRM/
  SIEM-shipping ports specifically) — flagged as a Phase 1 hardening
  follow-up in ADR 0003, not yet done.
