# Deliberate lab vulnerabilities

Every intentional weakness in this lab is listed here, with the MITRE ATT&CK
technique(s) it exists to exercise and a reference link. Items 1, 2, 3, 4, 6,
and 7 are now implemented in the `config/dc/` and `config/member/` Ansible
roles (see "Status" column) — but **not yet run-tested**: there is no local
WinRM-reachable Windows host to execute against (`infra/local` hasn't been
built, see [ROADMAP.md](../ROADMAP.md)). Items 5 and 8 remain deferred (see
"Design notes"). This file is required reading before touching `config/dc/`
or `config/member/` — every misconfiguration those roles apply must have a
corresponding row here (required by
[CONTRIBUTING.md](../CONTRIBUTING.md)).

No misconfiguration here is a novel technique — each is a well-known,
publicly documented AD weakness. The lab's job is to instantiate them
realistically, not invent new ones (see [SECURITY.md](../SECURITY.md) #3).

| # | Misconfiguration | Where | ATT&CK technique(s) | Status |
|---|---|---|---|---|
| 1 | Service account with an SPN set and a weak/crackable password (Kerberoastable) | `svc-sql` on `dc01` | [T1558.003 — Kerberoasting](https://attack.mitre.org/techniques/T1558/003/) | Implemented in `config/dc/tasks/misconfigs.yml` — not run-tested |
| 2 | User account with Kerberos pre-authentication disabled (AS-REP roastable) | `svc-legacy` on `dc01` | [T1558.004 — AS-REP Roasting](https://attack.mitre.org/techniques/T1558/004/) | Implemented in `config/dc/tasks/misconfigs.yml` — not run-tested |
| 3 | Member server configured for unconstrained Kerberos delegation | `mem01` | [T1558 — Steal or Forge Kerberos Tickets](https://attack.mitre.org/techniques/T1558/) (ticket capture after coerced auth via [T1187 — Forced Authentication](https://attack.mitre.org/techniques/T1187/)) | Implemented in `config/dc/tasks/post_join_misconfigs.yml` — not run-tested |
| 4 | Low-privilege user granted `GenericAll`/`WriteDACL`/`ForceChangePassword` on a higher-privilege object (BloodHound-style ACL abuse path) | `dc01` (AD DACLs) | [T1098 — Account Manipulation](https://attack.mitre.org/techniques/T1098/); when it grants replication rights, escalates to [T1003.006 — DCSync](https://attack.mitre.org/techniques/T1003/006/) | Implemented in `config/dc/tasks/misconfigs.yml` — not run-tested |
| 5 | Local administrator password reused across `mem01` and a workstation | `mem01`, `wks01` | [T1078.003 — Valid Accounts: Local Accounts](https://attack.mitre.org/techniques/T1078/003/), [T1550.002 — Pass the Hash](https://attack.mitre.org/techniques/T1550/002/) | **Deferred** — needs a 2nd non-DC Windows host, see note below |
| 6 | Low-privilege group granted edit rights on a GPO linked to a sensitive OU | `dc01` (Group Policy) | [T1484.001 — Domain Policy Modification: Group Policy Modification](https://attack.mitre.org/techniques/T1484/001/) | Implemented in `config/dc/tasks/misconfigs.yml` — not run-tested |
| 7 | Credentials left in a plaintext script/config on a SYSVOL-adjacent share | `dc01` (SYSVOL) | [T1552.001 — Unsecured Credentials: Credentials In Files](https://attack.mitre.org/techniques/T1552/001/) | Implemented in `config/dc/tasks/misconfigs.yml` — not run-tested |
| 8 | A synthetic Domain Admin has an active/cached session on a workstation-tier host | `wks01` | Enables [T1003.001 — OS Credential Dumping: LSASS Memory](https://attack.mitre.org/techniques/T1003/001/) after initial workstation compromise, feeding [T1021.002 — SMB/Windows Admin Shares](https://attack.mitre.org/techniques/T1021/002/) lateral movement | **Deferred** — needs a 2nd non-DC Windows host, see note below |

## Design notes

- Items 1–2 and 4 are the ones the attack chains in Phase 3 are expected to
  exercise first, since they map directly to the most common real-world AD
  compromise path (Kerberoast/AS-REP roast for initial creds → ACL abuse for
  privesc → DCSync for domain dominance) and each has a well-understood
  Sigma detection story for Phase 4.
- **Items 5 and 8 are deferred, not planned, following the footprint trim in
  [ADR 0004](adr/0004-revert-to-local-utm.md).** Both originally depended on
  a `wks01` workstation distinct from `mem01`, so that "local admin reuse"
  and "cached Domain Admin session" each had two non-DC hosts to connect. With
  only `dc01` + `mem01` in the trimmed local footprint, the recon → initial
  access → credential access → lateral movement → domain dominance chain
  still runs end-to-end using item 3 instead: unconstrained delegation on
  `mem01` gives a `mem01` compromise a path to capture a ticket and reach
  `dc01`, without needing a workstation hop. Reintroducing `wks01` (a
  documented option, not a dropped requirement — see ADR 0004) re-enables
  items 5 and 8 as an additional, more realistic chain alongside item 3's.
- All passwords/credentials involved are generated per-deploy or drawn from
  `.env` — never hardcoded real-looking secrets committed to this repo
  (SECURITY.md #5).
