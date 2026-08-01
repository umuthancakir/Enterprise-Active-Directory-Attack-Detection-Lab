# ADR 0001: Deploy target is Azure

- **Status:** accepted
- **Date:** 2026-08-01

## Context

The lab needs to run genuine Windows Server hosts (a Domain Controller and
member servers) so that AD attack techniques and their telemetry are
authentic, not simulated. The build host is an Apple Silicon (arm64) Mac.

Detected locally: VirtualBox (`VBoxManage`) and UTM.app (QEMU-based). Not
present: Vagrant, libvirt/virsh, Terraform, Docker, Ansible, Packer, Azure
CLI, Homebrew.

Constraints specific to this host:

- **VirtualBox on Apple Silicon has no reliable Windows-guest support.**
  VirtualBox for arm64 macOS is still explicitly marked experimental by
  Oracle, and it has no hardware-assisted virtualization path for running
  x86_64 Windows guests on an ARM host. This rules out the "obvious" default
  from the project brief (Vagrant + VirtualBox) on this machine.
- **Microsoft does not publish ARM64 Windows Server ISOs through normal
  public channels.** Only x86_64 Windows Server media is generally
  available; ARM64 builds exist but are gated behind OEM/Insider programs,
  which is not reproducible or documentable for a public portfolio repo.
- **UTM/QEMU could emulate x86_64 Windows Server**, but full-system
  emulation (TCG, no hardware acceleration for a foreign architecture) is
  slow enough to make iterative provisioning and CI-style rebuilds
  impractical.
- This account additionally lacks sudo/admin rights on the host machine
  (confirmed: the Homebrew installer fails with "Need sudo access"), which
  independently blocks installing any local hypervisor tooling until an
  admin acts.

## Decision

`DEPLOY_TARGET=azure`. Terraform (`infra/azure/`) provisions an isolated
resource group and virtual network in Azure with real x86_64 Windows Server
VMs at native speed. The `local` target (UTM/QEMU or Vagrant+VirtualBox) is
left as documented-but-unimplemented in code, gated the same way the project
brief gates Azure — selectable via `DEPLOY_TARGET`, but not built until
there's a host where it's actually practical.

## Alternatives considered

- **UTM/QEMU, x86_64 emulation.** Local and free; genuine Windows Server
  fidelity. Rejected as the default because TCG emulation is slow enough to
  hurt the iterate-and-rebuild workflow this project depends on. Left as a
  documented future option for `DEPLOY_TARGET=local`.
- **UTM, native ARM64 Windows Server.** Best local performance. Rejected
  because ARM64 Windows Server media isn't available through normal public
  channels, which would make the setup non-reproducible for anyone cloning
  this repo.
- **Vagrant + VirtualBox (the brief's stated local default).** Rejected for
  this host specifically: VirtualBox's arm64 macOS support does not extend
  to running Windows guests reliably.

## Consequences

- Provisioning requires an Azure subscription and incurs cloud spend while
  the lab is up; `make down` must reliably tear everything down to bound
  cost.
- Network isolation invariant (SECURITY.md #1) is implemented via Azure NSGs
  and a vnet with no route to the internet or other Azure resources, rather
  than host-only networking on a hypervisor.
- Any future `DEPLOY_TARGET=local` implementation should target a host with
  either an Intel Mac, a Linux host with KVM, or a Windows host with
  Hyper-V/WSL2 — not documented as supported on Apple Silicon.
- Local `terraform apply` cannot run yet on this build machine (see ADR
  context re: no sudo); `infra/azure/` is being written and validated for
  syntax only until an admin installs the required CLI tooling or the
  operator runs it from a different machine.
