# IR Playbook: DCSync

Aligned to [NIST SP 800-61 Rev. 2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf).
Detects the final step of `attack/chains.py`'s `domain_dominance` chain —
[`attack/techniques.py`](../../attack/techniques.py)'s `dcsync` technique
([T1003.006](https://attack.mitre.org/techniques/T1003/006/)). **This is
the most severe playbook in this set — a successful DCSync means full
domain compromise.**

## 1. Preparation

- Windows Security auditing: **Directory Service Access** subcategory,
  plus a SACL on the domain naming context for the
  `DS-Replication-Get-Changes`/`-All` extended rights — see
  [`telemetry/windows-audit-policy/configure-dcsync-sacl.ps1`](../../telemetry/windows-audit-policy/configure-dcsync-sacl.ps1).
  Without this specific SACL, DCSync is **completely invisible** — there
  is no other event source for it.
- Detection rule: [`detections/sigma/dcsync.yml`](../../detections/sigma/dcsync.yml).
  Note its filter excludes only `dc01$`'s own legitimate replication, not
  all machine accounts — see that rule's comments for why (this lab's own
  `dcsync` technique uses a captured `mem01$` ticket, which a broader
  filter would incorrectly hide).
- Know your legitimate replication principals: real DCs, and (in
  environments that have it) directory-sync tools like Azure AD Connect.
  Anything replicating that isn't on that list is the finding.

## 2. Detection & Analysis

**Trigger:** event 4662 carrying the `DS-Replication-Get-Changes` or
`DS-Replication-Get-Changes-All` extended-right GUID, from a principal
that is not `dc01$` (or another known-legitimate replication account).

**Initial triage — treat this as a confirmed high-severity incident by
default**, not a hypothesis to prove first. Unlike the other playbooks in
this set, DCSync at the "any account replicated domain secrets" level is
close to always the outcome of a completed attack chain, not ambiguous
background noise:

1. Identify the principal that performed the replication
   (`SubjectUserName` on the 4662). In this lab's `domain_dominance`
   chain, this is `MEM01$` — a captured computer-account ticket, not a
   human user account, which is itself an anomaly worth noting (real
   attacks often use a compromised human account's credentials instead;
   both patterns matter).
2. Determine what was replicated. `secretsdump.py -just-dc` (the tool this
   lab's technique uses) pulls the full domain credential database — treat
   this as **every credential in the domain being compromised**, not just
   the account that performed the request.
3. Work backward through the chain: how did the acting principal obtain
   replication rights in the first place? In this lab, via
   `unconstrained_delegation_coerce` capturing a DC ticket — see that
   playbook. In a real incident, also check for a direct ACL grant path
   (see `acl-abuse.md`) as an alternative root cause.

## 3. Containment, Eradication & Recovery

**This phase is domain-wide, not account-scoped — treat it accordingly.**

1. **Contain:** isolate the host/account that performed the replication
   immediately. If it was a captured computer-account ticket (as in this
   lab), that ticket remains valid until its natural expiry or a forced
   krbtgt rotation — isolation of the source host alone is not sufficient
   containment.
2. **Eradicate — krbtgt rotation (twice):** the krbtgt account's password
   must be reset **twice**, with enough time between resets for
   replication to converge, to fully invalidate all outstanding Kerberos
   tickets domain-wide (a single reset leaves the previous password's
   tickets valid due to krbtgt password history). This is the step that
   actually closes out a DCSync exposure — nothing less does.
   Also rotate every credential that was in the replicated database in
   practice (at minimum: all privileged accounts; a full domain-wide
   credential reset is the textbook-correct but operationally heavy
   answer, and the actual scope should be a risk-based call, not skipped
   entirely).
3. **Recover:** re-enable/restore isolated hosts only after krbtgt
   rotation is complete and verified. Monitor closely for any sign the
   attacker retained a separate persistence mechanism established using
   the replicated credentials before containment began.

## 4. Post-Incident Activity

- **Root cause, not just symptom:** DCSync itself is rarely the initial
  entry point — it's the culmination of a chain (in this lab,
  ACL-abuse-or-delegation-coercion → DCSync). Post-incident review must
  address the earlier stage(s), not just add more DCSync-specific
  monitoring.
- **Hardening:** ensure `DS-Replication-Get-Changes`/`-All` rights are
  granted only to the built-in DC-related principals and any explicitly
  required directory-sync service account — audit this the same way as
  any other standing high-privilege grant.
- This playbook, `acl-abuse.md`, and `unconstrained-delegation.md`
  together model this lab's full `domain_dominance` attack chain — review
  them as one narrative when writing the incident report, not three
  disconnected events.
