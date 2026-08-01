# ADR 0003: Network isolation model on Azure

- **Status:** superseded by [ADR 0005](0005-local-network-isolation.md) (deploy target reverted to local — see [ADR 0004](0004-revert-to-local-utm.md))
- **Date:** 2026-08-01

## Context

SECURITY.md invariant #1 requires the lab network to have "no route to the
internet or any third-party system." On a hypervisor with host-only
networking that's straightforward — the virtual switch simply isn't bridged.
On Azure, "no route to the internet" needs a precise definition, because two
things are easy to conflate:

1. The lab's own hosts (DC, member server, workstation, attacker box, SIEM)
   reaching outbound to the internet or to anything outside the lab vnet.
2. The operator reaching *inbound* into the lab vnet to manage/provision it.

Additionally, every Azure VM — regardless of NSG rules — talks to a
platform-owned endpoint (`168.63.129.16`, Azure's "WireServer"/host channel)
for the guest agent, extensions, and IMDS. This is not internet access and
not configurable per-VM; it's how Azure IaaS works for any VM, isolated or
not, and it's how Terraform/Ansible-driven provisioning (custom script
extension, DSC extension) reaches the guest without needing the guest to have
a public IP or internet route.

## Decision

- **No lab VM (DC, member, workstation, attacker, SIEM) has a public IP.**
  All are on a single `lab-subnet` inside an isolated vnet.
- **NSG on `lab-subnet` denies all outbound to the `Internet` service tag**
  and denies all inbound from `Internet`. The only allowed traffic is: (a)
  within the vnet (`VirtualNetwork` ↔ `VirtualNetwork`), and (b) from the
  `AzureBastionSubnet`, restricted to the specific management ports each
  role needs (RDP/WinRM for Windows hosts, SSH for Linux hosts).
- **Azure Bastion** provides the operator's only path into the environment,
  in its own `AzureBastionSubnet`. Bastion is a managed jump service — it
  terminates the operator's HTTPS session from the Azure Portal/CLI and
  proxies RDP/SSH into the vnet; the lab VMs are never directly exposed.
  This is the "genuinely blocking input aside" case where a small amount of
  inbound *management* surface is unavoidable and appropriate — it's
  equivalent to walking up to a physically isolated lab with a keyboard, not
  a hole in the lab's containment.
- **The Azure platform channel (`168.63.129.16`) is explicitly out of scope
  of the "no internet" invariant.** It is Azure-fabric-only, not
  internet-routable, not attacker-reachable, and required for any Azure VM
  to function. This is documented here so it's never mistaken for an
  isolation gap during review.
- Attack tooling runs *from* the attacker VM, inside the vnet — it never
  needs to reach the lab hosts from outside, so the scope guard
  (`inventory/lab-scope.yaml`, ADR 0002) and the network isolation are
  independent, layered controls rather than one substituting for the other.

## Alternatives considered

- **Public IP + NSG allow-list per VM, no Bastion.** Rejected: every lab VM
  would need a real public IP, which is a materially bigger attack surface
  than a single managed Bastion host, and contradicts "no route to the
  internet" much more directly.
- **VPN gateway for operator access instead of Bastion.** More setup and
  cost (a gateway SKU running continuously) for equivalent isolation
  properties at this lab's scale. Reconsider if multi-operator access is
  ever needed.
- **No operator access path at all; manage everything via `terraform apply`
  + extensions only.** Rejected: useful for initial provisioning, but
  detection engineering work benefits from being able to RDP into a host and
  look around by hand. Bastion keeps that possible without weakening
  isolation.

## Consequences

- `infra/azure/network.tf` must create `AzureBastionSubnet` with the exact
  name and `/26`-or-larger prefix Azure requires, plus the Bastion resource
  and its own public IP (the *only* public IP in the deployment).
- `make down` must destroy Bastion along with everything else — it is billed
  hourly while running and is not something to leave up between sessions.
- CI's `terraform validate` will catch drift here, but the "no route to
  Internet" property itself is only enforced by NSG rules, which should be
  covered by a `terraform plan` review checklist item (and ideally an
  automated NSG-rule assertion) called out in Phase 1's definition of done.
