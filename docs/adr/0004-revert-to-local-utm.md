# ADR 0004: Revert deploy target to local UTM/QEMU

- **Status:** accepted
- **Date:** 2026-08-01

## Context

[ADR 0001](0001-deploy-target.md) chose `DEPLOY_TARGET=azure` on the
reasoning that VirtualBox has no reliable Windows-guest support on Apple
Silicon and ARM64 Windows Server media isn't publicly available, and that
UTM/QEMU x86_64 emulation would be too slow for iterative use. The operator
picked Azure explicitly at that point, and `infra/azure/` (Terraform for
resource group, vnet, NSGs, Bastion, and all 5 VMs) plus ADR 0003 (the
Azure network isolation model) were built out — code only, never applied;
no `az login` was ever run in this build (verified: `az` CLI still isn't
on PATH, there's no credential error in this session's history).

The operator has now reconsidered and asked to revert to local UTM/QEMU
with a trimmed footprint, independent of any Azure failure. Reasons this is
a reasonable call even though the original tradeoff analysis in ADR 0001
stands:

- No ongoing cloud cost or credential/subscription dependency for a
  portfolio project that should be cloneable and runnable by a reviewer
  without an Azure account.
- The "too slow" concern in ADR 0001 is mitigated by trimming the footprint:
  drop the standalone workstation VM and keep only what the core attack
  chain needs (DC + one member server, both x86_64-emulated Windows Server),
  while the attacker box and SIEM host run as **native ARM64 Linux** (Kali
  and Ubuntu both ship ARM64 builds) — no emulation overhead on the two
  hosts that see the most I/O (tool execution, log ingestion).

## Decision

`DEPLOY_TARGET=local`, implemented via Packer (QEMU builder) to produce base
VM images and a small Python generator (`infra/local/generate_bundles.py`)
that assembles UTM `.utm` bundles from those images, rather than Terraform.
`infra/azure/` is removed from the tree (recoverable from git history at
commit `67ce0f3` if ever needed again) in favor of `infra/local/`.

Footprint trimmed from the original 5-host design to 4 hosts:

| Host | Role | Arch | Why |
|---|---|---|---|
| `dc01` | Domain Controller | x86_64 (emulated) | Windows Server has no practical ARM64 path — see ADR 0001 |
| `mem01` | Member server | x86_64 (emulated) | same |
| `attacker01` | Attacker box (Kali) | arm64 (native) | Kali ships ARM64 builds; no emulation cost |
| `siem01` | SIEM host | arm64 (native) | Ubuntu ships ARM64 builds; no emulation cost |

The standalone `wks01` workstation is dropped for now. This shortens the
attack chain to DC ↔ member only (recon → initial access on `mem01` →
credential access → domain dominance on `dc01`), which is still a complete
and realistic path — see the corresponding update to
[`docs/vulnerabilities.md`](../vulnerabilities.md). Reintroducing a
workstation later (as a 3rd emulated Windows VM) is a documented option, not
a dropped requirement — tracked in ROADMAP.md.

## Alternatives considered

- **Keep Azure, work through credential setup when the operator is ready.**
  Rejected per explicit operator instruction; nothing about Azure had
  actually failed, this is a preference change, not a bug fix.
- **Native ARM64 Windows Server via Insider/eval channels for `dc01`/`mem01`
  too.** Still rejected for the same reproducibility reason as ADR 0001 —
  can't be documented as "clone and run" for a portfolio reviewer without
  Insider program access.
- **Terraform with a community UTM/libvirt provider.** Investigated
  conceptually: no official HashiCorp UTM provider exists, and UTM does not
  expose a declarative "create VM from spec" CLI — `utmctl` (UTM's
  scripting interface) can start/stop/inspect existing VMs but not
  originate them from a config file. Packer's QEMU builder *is* a
  legitimate, well-supported way to produce the qcow2 images UTM's VMs run
  on, so the pragmatic split is: Packer builds images (real IaC, testable),
  a small generator script assembles UTM bundles from them (thin glue, not
  pretending to be more than it is).

## Consequences

- **This does not remove the local-tooling blocker.** Packer, QEMU (for
  `qemu-img`/`qemu-system-aarch64` on PATH — separate from UTM's bundled
  copy), and Ansible still need Homebrew, which this account cannot install
  without an admin (same blocker recorded against the Azure path in
  BUILD_LOG.md). The pivot removes the Azure *credential/cost* dependency,
  not the *local admin rights* dependency.
- **No Terraform-style plan/diff or state tracking.** `generate_bundles.py`
  regenerating a bundle is idempotent (overwrites deterministically from
  the same inputs) but there is no equivalent of `terraform plan` showing
  what would change before it happens. This is a real capability gap
  against the Azure path and is called out here rather than glossed over.
- `inventory/lab-scope.yaml`, `scripts/sync_scope.py`, the root `Makefile`,
  `.env.example`, `README.md`, and `.github/workflows/ci.yml` all needed
  updates to stop assuming a Terraform/Azure backend — done alongside this
  ADR.
- The Ansible roles for AD DS promotion, domain join, and the 8 (now
  reduced to 7 directly-implementable, 1 deferred) misconfigurations are
  unaffected by this pivot — they target hosts by IP/role via
  `inventory/lab-scope.yaml`, not by cloud provider, so none of that work
  is lost.
