# IR Playbook: Directory ACL Abuse (GenericAll Grant)

Aligned to [NIST SP 800-61 Rev. 2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf).
Detects [`docs/vulnerabilities.md`](../../docs/vulnerabilities.md) item 4
and [`attack/techniques.py`](../../attack/techniques.py)'s
`acl_genericall_abuse` technique
([T1098](https://attack.mitre.org/techniques/T1098/)).

## 1. Preparation

- Windows Security auditing: **Directory Service Access** subcategory
  enabled, plus a SACL on the monitored object (`Domain-Backups` in this
  lab) — see
  [`telemetry/windows-audit-policy/configure-object-sacls.ps1`](../../telemetry/windows-audit-policy/configure-object-sacls.ps1).
  **Without the SACL specifically, no amount of audit-policy configuration
  produces an event for this object** — SACLs are per-object, not global.
  Verify: `(Get-Acl "AD:\<object DN>").Audit`.
- Detection rule: [`detections/sigma/acl_genericall_abuse.yml`](../../detections/sigma/acl_genericall_abuse.yml).
- Know your privileged-object ACL baseline. BloodHound (or equivalent)
  should be run periodically against production to catch *unintended*
  `GenericAll`/`WriteDACL`/`ForceChangePassword` grants before an attacker
  finds them via the same tooling.

## 2. Detection & Analysis

**Trigger:** event 4662 on the SACL-monitored object (`Domain-Backups`).

**Initial triage:**

1. Identify who performed the operation (`SubjectUserName` on the 4662)
   and what right was exercised (`AccessMask`/`Properties`). In this lab,
   `helpdesk-jsmith` holds a deliberately over-broad `GenericAll` grant —
   confirm the actor matches the account(s) actually authorized to hold
   that grant, if any are legitimately authorized at all.
2. Determine what the grant was actually used for: a password reset
   (`ForceChangePassword`-equivalent via `GenericAll`), a group membership
   change, or a DACL modification on the target object itself (which could
   chain into further privilege escalation). Event 5136
   ("directory service object was modified") complements 4662 with a
   readable before/after for this.
3. This is fundamentally a **privilege escalation** finding, not
   necessarily an "attack" in isolation — the interesting question is
   whether the actor's underlying access (here, `helpdesk-jsmith`'s
   credentials) was itself obtained illegitimately. Check for a preceding
   credential-access event (Kerberoasting/AS-REP roasting/phishing) that
   would explain how the actor came to control this account.

## 3. Containment, Eradication & Recovery

1. **Contain:** if the acting account's own credentials appear compromised
   (not just the grant being abused legitimately-but-inappropriately),
   disable that account immediately
   (`Disable-ADAccount -Identity helpdesk-jsmith`).
2. **Eradicate:** remove the unintended ACL grant:
   `dsacls "<target DN>" /R "EADADL\helpdesk-jsmith"` (or the equivalent
   PowerShell `Set-Acl` with the offending `ActiveDirectoryAccessRule`
   removed). Reset the password of any account whose credentials were
   changed via the abused grant.
3. **Recover:** verify the target object's effective permissions now match
   the intended baseline, and that any legitimately-affected service
   (e.g. whatever used the reset account) is restored.

## 4. Post-Incident Activity

- **Hardening (ties back to `docs/vulnerabilities.md` item 4):** this
  grant should never have existed without a documented business reason.
  Run BloodHound's "shortest path to Domain Admins" analysis periodically
  and treat any new edge as a change-control violation requiring
  justification, not just a technical finding to quietly fix.
- If the grant enabled a downstream privilege escalation (e.g. it was used
  to eventually reach replication rights — see the `dcsync.md` playbook),
  treat this as one incident spanning both playbooks, not two independent
  ones — the ACL abuse is the root cause, DCSync is the impact.
