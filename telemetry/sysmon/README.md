# Sysmon configuration

`sysmon-config.xml` is deployed to `dc01` and `mem01` (once `config/dc`/
`config/member` gain the Ansible task to do so — not yet added, see
ROADMAP.md Phase 2). It is intentionally narrow, not a copy of a
kitchen-sink community config: every include/exclude rule below exists
because it's relevant to a technique in `attack/techniques.py` or a
misconfiguration in `docs/vulnerabilities.md`, and the README explains
which.

## What it covers

| Event ID | What | Why (technique / misconfig it supports) |
|---|---|---|
| 1 — ProcessCreate | Every process launch, narrow exclude list only | Baseline visibility for any tooling run against a host — `kerberoasting`, `asrep_roasting`, `dcsync`, etc. all show up here as the process making the connection |
| 3 — NetworkConnect | SMB/LDAP/LDAPS/Kerberos/WinRM/RDP only | Lateral movement and the specific ports every technique in the registry actually uses |
| 10 — ProcessAccess (LSASS only) | Any process opening a handle to `lsass.exe` | T1003.001 credential dumping — the natural follow-on after `dcsync`/delegation-ticket chains |
| 11 — FileCreate (SYSVOL/NETLOGON only) | Files written under those paths | Directly ties to `docs/vulnerabilities.md` item 7 (plaintext creds in SYSVOL) |
| 12/13/14 — RegistryEvent | Run keys + Services only | Cheap, standard persistence coverage |
| 19/20/21 — WmiEvent | All | Low volume in a lab this size; WMI persistence/lateral movement is worth catching outright |
| 22 — DnsQuery | All | Recon-phase signal (bulk LDAP/DNS lookups during `bloodhound_collect`) |

## What it deliberately does NOT cover

Sysmon cannot see Kerberos ticket request/issuance content or Active
Directory object-level access (ACL reads/writes, replication requests).
That means **Kerberoasting (item 1), AS-REP roasting (item 2), the ACL
abuse in item 4, and DCSync are invisible to Sysmon alone** — they only
show up in Windows Security auditing events (4768/4769/4771, 4662/5136).
See [`telemetry/windows-audit-policy/`](../windows-audit-policy/README.md).
This split is deliberate and documented in
[ADR 0006](../../docs/adr/0006-telemetry-architecture.md) — a Sigma rule
in Phase 4 for any of those four misconfigs will source from the Security
channel, not from Sysmon.

## Status

Written, not deployed or validated against a real Sysmon install — no lab
host exists yet. Confirmed well-formed XML only (`xml.dom.minidom.parse`).
Targets Sysmon schema version 4.90 (Sysmon v15.x).
