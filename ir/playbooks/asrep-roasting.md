# IR Playbook: AS-REP Roasting

Aligned to [NIST SP 800-61 Rev. 2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf).
Detects [`docs/vulnerabilities.md`](../../docs/vulnerabilities.md) item 2
and [`attack/techniques.py`](../../attack/techniques.py)'s `asrep_roasting`
technique ([T1558.004](https://attack.mitre.org/techniques/T1558/004/)).

## 1. Preparation

- Windows Security auditing: **Kerberos Authentication Service**
  subcategory enabled on `dc01` — see
  [`telemetry/windows-audit-policy/configure-audit-policy.ps1`](../../telemetry/windows-audit-policy/configure-audit-policy.ps1).
  Verify with `auditpol /get /subcategory:"Kerberos Authentication Service"`.
- Detection rule: [`detections/sigma/asrep_roasting.yml`](../../detections/sigma/asrep_roasting.yml).
- Inventory accounts with `DoesNotRequirePreAuth` set:
  `Get-ADUser -Filter {DoesNotRequirePreAuth -eq $true} -Properties DoesNotRequirePreAuth`.
  `svc-legacy` (this lab's deliberately AS-REP-roastable account) should
  be the *only* hit — any other result is an undocumented finding on its
  own, independent of an active attack.

## 2. Detection & Analysis

**Trigger:** Sigma rule fires on event 4768 (TGT request) with
`PreAuthType = 0` — no pre-authentication was performed, meaning the AS-REP
was issued without the requester proving knowledge of the account's
password first.

**Initial triage:**

1. Unlike Kerberoasting, this technique needs **no valid credentials at
   all** — anyone who can reach the KDC (any domain-joined or even
   unauthenticated network position, depending on configuration) can
   request a TGT for a known AS-REP-roastable username and attempt to
   crack the response offline. Treat the mere existence of a 4768 with
   `PreAuthType = 0` as notable regardless of source reputation.
2. Identify the requesting source (`IpAddress` on the 4768). A source
   outside the expected set of domain-joined hosts is a stronger signal
   than internal noise.
3. As with Kerberoasting, a single 4768 only proves the AS-REP was
   requested, not cracked — correlate with subsequent successful/failed
   logons by the target account.

## 3. Containment, Eradication & Recovery

1. **Contain:** isolate the source host if identifiable and untrusted.
2. **Eradicate:** rotate the targeted account's password immediately (same
   rationale as Kerberoasting — invalidate the captured AS-REP for offline
   cracking). If the account's `DoesNotRequirePreAuth` flag is not a
   documented/intentional exception, clear it:
   `Set-ADAccountControl -Identity <account> -DoesNotRequirePreAuth $false`.
3. **Recover:** confirm any service/process depending on the account still
   authenticates correctly post-remediation.

## 4. Post-Incident Activity

- **Hardening (ties back to `docs/vulnerabilities.md` item 2):** pre-auth
  should be required for every account with no documented, reviewed
  exception. `svc-legacy` is intentionally left vulnerable in this lab to
  model a common real-world finding — legacy service accounts configured
  for compatibility with old Kerberos clients and never revisited.
- Note this technique requires no prior AD credentials — if it fired, the
  environment was reachable by an unauthenticated or minimally-privileged
  actor, which should raise the incident's overall severity assessment
  relative to Kerberoasting (which requires at least some valid domain
  credentials to enumerate SPNs in most configurations).
