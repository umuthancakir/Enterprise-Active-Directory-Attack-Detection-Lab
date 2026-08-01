# ADR 0006: Telemetry architecture — WEF collector + single winlogbeat shipper

- **Status:** accepted
- **Date:** 2026-08-01

## Context

Phase 4's detection library needs real telemetry to test Sigma rules
against, and Phase 3's attack techniques need somewhere their effects show
up. Two components generate the signal: Sysmon (process/network/file/
registry visibility beyond the built-in Windows event log) and Windows'
own Security auditing (specifically Kerberos ticket events 4768/4769/4771
and directory-service-access event 4662/5136 — Sysmon does not see
Kerberos ticket operations or AD object ACL/replication activity at all,
so it cannot stand alone for this lab's specific misconfigs).

Getting that telemetry off `dc01`/`mem01` and into `siem01` needs a
shipping mechanism. Two common patterns exist:

1. **Winlogbeat (or another shipper) installed on every source host**,
   each shipping directly to Elasticsearch.
2. **Windows Event Forwarding (WEF)**: source hosts forward selected
   event channels to a designated collector's `ForwardedEvents` log; a
   single shipper on the collector ships that consolidated log onward.

## Decision

Use WEF: `dc01` is the WEF collector (source-initiated subscription;
`mem01` is the only other Windows host and forwards to it), and a single
Winlogbeat instance on `dc01` ships `Microsoft-Windows-Sysmon/Operational`,
`Security`, and `ForwardedEvents` to Elasticsearch on `siem01`.

## Alternatives considered

- **Winlogbeat per host.** Simpler to reason about per-host, and more
  realistic for a larger environment. Rejected for this lab specifically
  because: (a) it's more install surface across `config/dc`+`config/member`
  for a 2-Windows-host lab where the difference barely matters, and (b) WEF
  is itself a technique worth demonstrating — real enterprise AD
  environments overwhelmingly use WEF or a commercial forwarder, not
  per-host shippers, so exercising the WEF configuration path has
  standalone teaching value for this project.
- **Sysmon alone, no Windows Security auditing.** Rejected outright — see
  Context. Kerberoasting (item 1), AS-REP roasting (item 2), and DCSync
  (part of the `domain_dominance` chain) are only visible through Windows
  Security events (4769, 4768/4771, 4662/5136 respectively), not Sysmon.
  `telemetry/windows-audit-policy/` exists specifically to make sure this
  isn't silently missed.

## Consequences

- `dc01` is both the domain's DNS server (ADR 0005) and now the WEF
  collector and the sole Winlogbeat shipper — a meaningful concentration of
  role on one host, acceptable for a lab that gets torn down and rebuilt
  per session but worth flagging explicitly rather than glossing over: a
  real production design would split these roles.
- `config/dc/` needs a follow-up Ansible task to install Winlogbeat and
  apply `telemetry/winlogbeat/winlogbeat.yml`, and `config/member/` needs
  one to configure WEF forwarding (GPO or direct `wecutil`/registry) — not
  yet added; see ROADMAP.md Phase 2.
- If `mem01`'s forwarding breaks, its telemetry silently stops reaching
  `siem01` with no separate alerting on that fact in this lab (a real SOC
  would monitor forwarder health) — documented as a known gap, not solved
  here.
