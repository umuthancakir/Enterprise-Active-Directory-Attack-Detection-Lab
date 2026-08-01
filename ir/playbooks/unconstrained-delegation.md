# IR Playbook: Unconstrained Delegation Coercion

Aligned to [NIST SP 800-61 Rev. 2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf).
Detects [`docs/vulnerabilities.md`](../../docs/vulnerabilities.md) item 3
and [`attack/techniques.py`](../../attack/techniques.py)'s
`unconstrained_delegation_coerce` technique
([T1187](https://attack.mitre.org/techniques/T1187/) forced authentication,
enabling [T1558](https://attack.mitre.org/techniques/T1558/) ticket theft).

## 1. Preparation

- Sysmon PipeEvent (event 17/18) coverage for `\PIPE\efsrpc`/`\PIPE\lsarpc`
  — see [`telemetry/sysmon/sysmon-config.xml`](../../telemetry/sysmon/sysmon-config.xml).
- Detection rule: [`detections/sigma/unconstrained_delegation_coerce.yml`](../../detections/sigma/unconstrained_delegation_coerce.yml).
- Inventory which computer objects have unconstrained delegation enabled:
  `Get-ADComputer -Filter {TrustedForDelegation -eq $true} -Properties TrustedForDelegation`.
  `mem01` (this lab's deliberately unconstrained-delegation host) should
  be a documented, deliberate exception — any undocumented result is its
  own finding.

## 2. Detection & Analysis

**Trigger:** a process accessed the `\PIPE\efsrpc` or `\PIPE\lsarpc` named
pipe — the MS-EFSR/MS-LSAT RPC interfaces PetitPotam-style coercion tools
use to force a target (typically a Domain Controller) to authenticate to
an attacker-controlled/attacker-influenced host.

**Initial triage:**

1. This is a **two-hop** technique: (a) coercion — forcing `dc01` to
   authenticate somewhere — and (b) capture — the unconstrained-delegation
   host (`mem01`) receiving and storing that authentication as a usable
   ticket. The Sigma rule here only covers (a); confirm whether `mem01`
   subsequently shows an unexpected TGT for `DC01$` in its ticket cache
   (`klist` on `mem01`, or a corresponding Kerberos event) as evidence (b)
   actually succeeded.
2. Identify the process that accessed the named pipe and the account
   context it ran under. A legitimate EFS/LSA operation is technically
   possible but should be rare/absent in a lab environment with no active
   EFS usage.
3. This finding, on its own, does not yet prove domain compromise — it
   proves an attempt to set up the conditions for a subsequent DCSync (see
   `dcsync.md`). Treat it as an early-stage finding that should trigger
   heightened monitoring on `mem01` and `dc01` for the next stage, not as
   a closed incident by itself.

## 3. Containment, Eradication & Recovery

1. **Contain:** if `mem01` (or whichever host is unexpectedly configured
   for unconstrained delegation) shows signs of active exploitation,
   isolate it — any TGT it captures for the DC can be used to fully
   compromise the domain (see `dcsync.md`).
2. **Eradicate:** remove unconstrained delegation from the host unless
   there is a specific, documented, reviewed business need:
   `Set-ADComputer -Identity <host> -TrustedForDelegation $false`. Prefer
   constrained delegation (`msDS-AllowedToDelegateTo`) or resource-based
   constrained delegation if delegation is genuinely required.
3. **Recover:** if a TGT for `DC01$` (or any DC) was captured, treat this
   as domain-compromising — proceed directly to the `dcsync.md` playbook's
   containment/eradication steps (krbtgt rotation, etc.), since a captured
   DC computer-account ticket is equivalent in impact to a completed
   DCSync.

## 4. Post-Incident Activity

- **Hardening (ties back to `docs/vulnerabilities.md` item 3):**
  unconstrained delegation is broadly considered a legacy feature that
  should not exist in a modern AD environment except in narrow,
  documented cases. Audit for it the same way you'd audit for any other
  standing privilege escalation path.
- Also apply the general PetitPotam/coercion mitigation: enable EPA
  (Extended Protection for Authentication) on AD CS endpoints if any
  exist, and ensure SMB signing is enforced — coercion techniques as a
  class are mitigated by not accepting unsigned/unauthenticated relay
  targets, independent of the delegation configuration itself.
