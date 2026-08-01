# IR Playbook: Kerberoasting

Aligned to [NIST SP 800-61 Rev. 2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf).
Detects [`docs/vulnerabilities.md`](../../docs/vulnerabilities.md) item 1
and [`attack/techniques.py`](../../attack/techniques.py)'s `kerberoasting`
technique ([T1558.003](https://attack.mitre.org/techniques/T1558/003/)).

## 1. Preparation

- Windows Security auditing: **Kerberos Service Ticket Operations**
  subcategory enabled on `dc01` — see
  [`telemetry/windows-audit-policy/configure-audit-policy.ps1`](../../telemetry/windows-audit-policy/configure-audit-policy.ps1).
  Without this, event 4769 isn't logged at all and this entire playbook is
  moot — verify first with `auditpol /get /subcategory:"Kerberos Service Ticket Operations"`.
- Detection rule: [`detections/sigma/kerberoasting.yml`](../../detections/sigma/kerberoasting.yml),
  proven against fixtures via `make detections-test`.
- Know your service accounts. `svc-sql` (this lab's deliberately
  Kerberoastable account) should be inventoried alongside every other
  SPN'd account (`setspn -Q */*` from any domain-joined host) — an
  unexpectedly large SPN inventory is itself a finding, independent of any
  single alert.

## 2. Detection & Analysis

**Trigger:** Sigma rule fires on event 4769 with `TicketEncryptionType =
0x17` (RC4) for a non-machine account.

**Initial triage:**

1. Identify the requesting account (`TargetUserName`/`SubjectUserName` on
   the 4769) and source host (`IpAddress`). A legitimate admin running
   `setspn`/BloodHound for inventory purposes looks identical at the event
   level — context (was this expected? from an authorized host?) is what
   separates hunting from incident.
2. Identify the targeted SPN account(s). One request against one account
   from an unfamiliar host is more likely a real attack than a bulk sweep
   from a known vulnerability-scanning host.
3. Check whether the ticket was actually used afterward (a 4769 alone only
   proves the ticket was *requested*, not that it was cracked or used —
   correlate with subsequent logons by the target service account from
   unexpected hosts).

**Scoping questions:**

- Is this `svc-sql` specifically, or a different SPN'd account not
  documented in `docs/vulnerabilities.md`? The latter means an
  undocumented/unintended Kerberoastable account exists and needs its own
  remediation, not just incident response.
- Single request or bulk roasting sweep (many 4769s, many different SPNs,
  short time window, one source)? Bulk sweep raises confidence this is
  automated tooling (`netexec --kerberoasting`, Rubeus, Impacket
  `GetUserSPNs.py`) rather than legitimate SPN inventory.

## 3. Containment, Eradication & Recovery

1. **Contain:** if the source host is identified and is not itself a
   trusted admin workstation, isolate it (network quarantine) to stop
   further ticket requests and any use of already-cracked credentials.
2. **Eradicate:** rotate the targeted service account's password
   immediately — this invalidates any offline-cracking effort against the
   already-captured ticket. Force a long, random password (service
   accounts should not have human-memorable passwords in the first place —
   see hardening below).
3. **Recover:** confirm the service(s) using the account still function
   post-rotation (update any hardcoded credential references). Re-enable
   the source host once confirmed clean, if it was quarantined.

## 4. Post-Incident Activity

- **Hardening (ties back to `docs/vulnerabilities.md` item 1):** every
  SPN'd account should have a long random password (25+ characters) or be
  a Group Managed Service Account (gMSA) with an automatically-rotated
  password — gMSAs are not practically Kerberoastable. `svc-sql` is
  intentionally left vulnerable in this lab; a real environment should not
  have any account matching this pattern.
- **Detection gap check:** did the Sigma rule fire promptly, or was this
  found via hunting instead? If hunting found it first, that's a detection
  pipeline gap (check `telemetry/wef/` forwarding health, `telemetry/winlogbeat/`
  shipping) worth its own follow-up, not just the account-level fix.
- Update the incident record with source host, account, and timeline for
  future correlation.
