# Deliberate lab vulnerabilities

Every intentional weakness in this lab is listed here, with the MITRE ATT&CK
technique(s) it exists to exercise and a reference link. This is a design
document as of this session: **none of these are implemented yet** — they
will be configured by the `config/*` Ansible roles in Phase 1
(`config/dc/`, `config/member/`), which have not been written. See
[ROADMAP.md](../ROADMAP.md) for current status. This file exists now so the
design is reviewable before implementation, and so every future Ansible
change that adds a misconfiguration has a corresponding row here rather than
being an undocumented surprise (required by [CONTRIBUTING.md](../CONTRIBUTING.md)).

No misconfiguration here is a novel technique — each is a well-known,
publicly documented AD weakness. The lab's job is to instantiate them
realistically, not invent new ones (see [SECURITY.md](../SECURITY.md) #3).

| # | Misconfiguration | Where | ATT&CK technique(s) | Status |
|---|---|---|---|---|
| 1 | Service account with an SPN set and a weak/crackable password (Kerberoastable) | `svc-sql` on `dc01` | [T1558.003 — Kerberoasting](https://attack.mitre.org/techniques/T1558/003/) | Planned |
| 2 | User account with Kerberos pre-authentication disabled (AS-REP roastable) | `svc-legacy` on `dc01` | [T1558.004 — AS-REP Roasting](https://attack.mitre.org/techniques/T1558/004/) | Planned |
| 3 | Member server configured for unconstrained Kerberos delegation | `mem01` | [T1558 — Steal or Forge Kerberos Tickets](https://attack.mitre.org/techniques/T1558/) (ticket capture after coerced auth via [T1187 — Forced Authentication](https://attack.mitre.org/techniques/T1187/)) | Planned |
| 4 | Low-privilege user granted `GenericAll`/`WriteDACL`/`ForceChangePassword` on a higher-privilege object (BloodHound-style ACL abuse path) | `dc01` (AD DACLs) | [T1098 — Account Manipulation](https://attack.mitre.org/techniques/T1098/); when it grants replication rights, escalates to [T1003.006 — DCSync](https://attack.mitre.org/techniques/T1003/006/) | Planned |
| 5 | Local administrator password reused across `mem01` and `wks01` | `mem01`, `wks01` | [T1078.003 — Valid Accounts: Local Accounts](https://attack.mitre.org/techniques/T1078/003/), [T1550.002 — Pass the Hash](https://attack.mitre.org/techniques/T1550/002/) | Planned |
| 6 | Low-privilege group granted edit rights on a GPO linked to a sensitive OU | `dc01` (Group Policy) | [T1484.001 — Domain Policy Modification: Group Policy Modification](https://attack.mitre.org/techniques/T1484/001/) | Planned |
| 7 | Credentials left in a plaintext script/config on a SYSVOL-adjacent share | `dc01` (SYSVOL) | [T1552.001 — Unsecured Credentials: Credentials In Files](https://attack.mitre.org/techniques/T1552/001/) | Planned |
| 8 | A synthetic Domain Admin has an active/cached session on `wks01` (a workstation-tier host) | `wks01` | Enables [T1003.001 — OS Credential Dumping: LSASS Memory](https://attack.mitre.org/techniques/T1003/001/) after initial workstation compromise, feeding [T1021.002 — SMB/Windows Admin Shares](https://attack.mitre.org/techniques/T1021/002/) lateral movement | Planned |

## Design notes

- Items 1–2 and 4 are the ones the attack chains in Phase 3 are expected to
  exercise first, since they map directly to the most common real-world AD
  compromise path (Kerberoast/AS-REP roast for initial creds → ACL abuse for
  privesc → DCSync for domain dominance) and each has a well-understood
  Sigma detection story for Phase 4.
- Item 8 exists specifically to make the recon → initial access →
  credential access → lateral movement → domain dominance chain from the
  project brief actually reachable end-to-end from a compromised
  workstation, rather than requiring a hop straight to the DC.
- All passwords/credentials involved are generated per-deploy or drawn from
  `.env`/`terraform.tfvars` — never hardcoded real-looking secrets committed
  to this repo (SECURITY.md #5).
