# ADR 0005: Local network isolation model (UTM host-only)

- **Status:** accepted
- **Date:** 2026-08-01

## Context

With the deploy target reverted to local UTM/QEMU ([ADR 0004](0004-revert-to-local-utm.md)),
the Azure vnet/NSG/Bastion isolation model from [ADR 0003](0003-azure-network-isolation.md)
no longer applies. UTM (on top of Apple's `vmnet.framework`) offers a
"Host Only" network mode per VM: the guest can reach the host and other
guests on the same host-only segment, with no route out to the internet or
the operator's LAN. This is the direct local equivalent of the isolation
property SECURITY.md invariant #1 requires.

## Decision

- Every lab VM (`dc01`, `mem01`, `attacker01`, `siem01`) is configured in
  its `.utm` bundle with a single network adapter in **Host Only** mode, all
  sharing the same UTM host-only network segment (`generate_bundles.py`
  writes the same `IF` name into each bundle's `config.plist` so they land
  on one shared segment rather than four isolated ones).
- The operator's Mac (the host) can reach every lab VM — this is the local
  equivalent of the "Bastion" access path from ADR 0003: there's no separate
  jump host because the host machine itself is the trusted access point,
  and it was never on the guests' network to begin with, so no additional
  proxy is needed.
- No lab VM gets a "Shared Network" (NAT-to-internet) adapter. This is the
  enforcement point for SECURITY.md #1 on this deploy target — reviewers
  checking isolation should look for the absence of a `VirtioNetworkNat`
  (or equivalent NAT) network device in each generated `config.plist`.
- Ansible reaches the Windows hosts over WinRM and the Linux hosts over SSH
  using their host-only IPs (assigned via DHCP on the host-only segment and
  recorded by `generate_bundles.py` into `infra/local/state.json`, which
  `scripts/sync_scope.py` reads to update `inventory/lab-scope.yaml` — see
  the updated ADR 0002 mechanism description).

## Alternatives considered

- **Bridged networking (VM appears on the operator's real LAN).** Rejected
  outright — directly violates isolation; a misconfigured or compromised
  lab host would be reachable from (and could reach) the operator's actual
  network.
- **Shared/NAT networking with an egress-blocking firewall layered on top.**
  More moving parts (pf rules on macOS, which need admin rights this
  account doesn't have) to reach a weaker guarantee than Host Only provides
  natively. Rejected as unnecessary complexity.

## Consequences

- All 4 lab VMs must be on the *same* UTM host-only segment or they can't
  reach each other (AD/Kerberos/SMB between `dc01`/`mem01`, tooling from
  `attacker01`, log shipping to `siem01`) — this is a hard requirement on
  `generate_bundles.py`, not just a default.
- Because host-only networking has no external DHCP/DNS beyond what
  `vmnet.framework` provides, `dc01` (once promoted) becomes the DNS server
  for the lab segment — `mem01`/`attacker01`/`siem01` must be configured to
  point their DNS resolution at `dc01`'s host-only IP, handled in the
  `config/member` Ansible role's network setup tasks.
- Teardown (`make down`) must delete the `.utm` bundle directories, which
  releases the host-only DHCP leases along with them — this is how
  "ephemeral" (SECURITY.md #4) is satisfied on this deploy target.
