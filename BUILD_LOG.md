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
