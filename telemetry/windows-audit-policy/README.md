# Windows Security auditing

Sysmon ([`telemetry/sysmon/`](../sysmon/README.md)) cannot see Kerberos
ticket operations, Active Directory object access/replication, or (by
default) filesystem reads. Six of this lab's misconfigs — Kerberoasting
(item 1), AS-REP roasting (item 2), the ACL abuse (item 4), the GPO
edit-rights abuse (item 6), the SYSVOL plaintext credential read (item 7),
and DCSync (the last step of the `domain_dominance` attack chain) — are
**only** visible through Windows' own Security auditing. This directory
configures that. See
[ADR 0006](../../docs/adr/0006-telemetry-architecture.md) for why this
split exists.

## Scripts

| Script | Enables | Feeds detection of |
|---|---|---|
| `configure-audit-policy.ps1` | 7 Advanced Audit Policy subcategories (Kerberos Authentication Service, Kerberos Service Ticket Operations, Directory Service Access, Directory Service Changes, Security Group Management, User Account Management, File System) | Baseline — the other scripts' SACLs produce nothing without this |
| `configure-dcsync-sacl.ps1` | SACL on the domain naming context for the `DS-Replication-Get-Changes[-All]` extended rights | DCSync (`attack/techniques.py`'s `dcsync` technique) |
| `configure-object-sacls.ps1` | SACL on the `Domain-Backups` group for WriteDacl/WriteProperty/GenericAll | Item 4's ACL abuse (`acl_genericall_abuse` technique) |
| `configure-gpo-sacl.ps1` | SACL on the `Lab-Workstation-Baseline` GPO's AD object for WriteProperty/WriteDacl | Item 6's GPO edit-rights abuse (`gpo_edit_abuse` technique) |
| `configure-sysvol-file-sacl.ps1` | **Filesystem** (not AD) SACL on the planted `map-network-drive.ps1` script for `ReadData` | Item 7's plaintext-credential read (`sysvol_credential_read` technique) |

Run `configure-audit-policy.ps1` first — the other scripts add SACLs that
produce events only once the corresponding audit subcategory is on.

## Event ID reference

| Event ID | Channel | What | Misconfig / technique |
|---|---|---|---|
| 4768 | Security | TGT requested | AS-REP roasting (item 2) — look for missing/zero pre-auth type |
| 4769 | Security | Service ticket requested | Kerberoasting (item 1) — look for RC4 (`0x17`) encryption type on an SPN'd account |
| 4662 | Security | Operation performed on an AD object | DCSync (via the replication-rights SACL) and item 4's ACL abuse (via the `Domain-Backups` SACL) |
| 5136 | Security | AD object modified | Complements 4662 with before/after values; also the source for item 6's GPO edit-rights abuse (via the GPO object SACL) |
| 4663 | Security | An attempt was made to access an object | Item 7's SYSVOL credential read (via the filesystem SACL) — the **only** event ID in this reference that's a filesystem event, not a directory-service one |

## Status

All five scripts are written but **not run against a real domain** — no
lab host exists yet (see ROADMAP.md). The DCSync extended-rights GUIDs in
`configure-dcsync-sacl.ps1` are the widely-published values for
`DS-Replication-Get-Changes`/`-All`; verify them against a live schema
before trusting them in a real deployment, per that script's own comment.

## Not done / follow-up

- These scripts aren't wired into `config/dc`'s Ansible role yet — running
  them is currently a manual step. Should become
  `config/dc/tasks/telemetry.yml` in a follow-up session.
