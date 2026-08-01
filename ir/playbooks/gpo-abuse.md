# IR Playbook: GPO Edit-Rights Abuse

Aligned to [NIST SP 800-61 Rev. 2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf).
Detects [`docs/vulnerabilities.md`](../../docs/vulnerabilities.md) item 6
and [`attack/techniques.py`](../../attack/techniques.py)'s
`gpo_edit_abuse` technique
([T1484.001](https://attack.mitre.org/techniques/T1484/001/)).

## 1. Preparation

- Windows Security auditing: **Directory Service Changes** subcategory,
  plus a SACL on the GPO's AD object — see
  [`telemetry/windows-audit-policy/configure-gpo-sacl.ps1`](../../telemetry/windows-audit-policy/configure-gpo-sacl.ps1).
  Without the SACL, GPO modifications are invisible regardless of audit
  policy — SACLs are per-object.
- Detection rule: [`detections/sigma/gpo_edit_abuse.yml`](../../detections/sigma/gpo_edit_abuse.yml).
  Deliberately unfiltered by actor (see that rule's `falsepositives` note)
  — every GPO change in this lab's small population is worth reviewing.
- Know your GPO edit-rights baseline:
  `Get-GPPermission -All -TargetType Group | Where-Object { $_.Permission -match "Edit" }`
  should return only actual GPO administrators. `HelpDesk-L1` (this lab's
  deliberately over-permissioned group) should be the only unexpected
  entry.

## 2. Detection & Analysis

**Trigger:** event 5136 on a `groupPolicyContainer` object.

**Initial triage:**

1. Identify the actor (`SubjectUserName`) and what changed. GPO changes
   are broad — a new computer/user preference, a script link, a registry
   setting, a security filter change, or a permission change on the GPO
   itself are all plausible and each imply a different follow-on impact.
2. **The real impact isn't the edit event itself — it's what happens on
   the next `gpupdate`/policy refresh cycle on every computer the GPO
   applies to.** A malicious scheduled task, startup script, or registry
   preference pushed via GPO propagates to every linked computer
   automatically, without the attacker touching those hosts directly.
   Identify the GPO's link scope (`Get-GPInheritance -Target <OU DN>`) to
   determine blast radius before assuming this is contained to one host.
3. As with `acl-abuse.md`, ask how the actor obtained edit rights in the
   first place — an unintended grant (item 6 itself) versus a compromised
   account that's a legitimate GPO admin are different root causes with
   different remediation.

## 3. Containment, Eradication & Recovery

1. **Contain:** if the change already propagated, isolate affected hosts
   showing signs of the pushed payload executing (correlate with Sysmon
   process-creation events matching the planted task/script).
2. **Eradicate:** revert the GPO change
   (`Restore-GPO` from a known-good backup, or manually remove the
   specific setting/task/script added). Remove the unintended edit-rights
   grant: `Set-GPPermission -Name <GPO> -TargetName <group> -TargetType Group -PermissionLevel None`.
3. **Recover:** force a policy refresh (`gpupdate /force`) on affected
   hosts to push the reverted GPO, and confirm the malicious artifact is
   actually gone (a `gpupdate` doesn't retroactively undo an already-run
   scheduled task or already-changed setting on its own).

## 4. Post-Incident Activity

- **Hardening (ties back to `docs/vulnerabilities.md` item 6):** GPO edit
  rights should be granted only to a small, reviewed set of actual policy
  administrators — treat any grant to a help-desk-tier group as a finding
  on its own, independent of whether it's ever actively abused.
- GPO changes affect every linked computer at once — this is one of the
  highest blast-radius findings in this lab's set relative to how little
  privilege it technically requires (`HelpDesk-L1` is not a privileged
  group by name). Don't let the low starting privilege understate the
  post-incident severity assessment.
