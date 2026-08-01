# IR Playbook: SYSVOL Plaintext Credential Exposure

Aligned to [NIST SP 800-61 Rev. 2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf).
Detects [`docs/vulnerabilities.md`](../../docs/vulnerabilities.md) item 7
and [`attack/techniques.py`](../../attack/techniques.py)'s
`sysvol_credential_read` technique
([T1552.001](https://attack.mitre.org/techniques/T1552/001/)).

## 1. Preparation

- Windows Security auditing: **File System** subcategory, plus a
  filesystem SACL on the specific planted script — see
  [`telemetry/windows-audit-policy/configure-sysvol-file-sacl.ps1`](../../telemetry/windows-audit-policy/configure-sysvol-file-sacl.ps1).
  This is the only item in this lab's misconfig set detected via a
  **filesystem** event (4663) rather than a directory-service one — don't
  assume the same audit subcategories that cover items 1–6 also cover
  this; they don't.
- Detection rule: [`detections/sigma/sysvol_credential_read.yml`](../../detections/sigma/sysvol_credential_read.yml).
- **SYSVOL is readable by every authenticated domain user by design** (it
  has to be, for Group Policy and logon scripts to function) — so unlike
  most other findings in this set, "who can reach this" isn't the
  interesting question. Any authenticated user reading this specific file
  is a hit worth reviewing.

## 2. Detection & Analysis

**Trigger:** event 4663 (`ReadData`) on
`...\SYSVOL\domain\scripts\map-network-drive.ps1`.

**Initial triage:**

1. Identify the reader (`SubjectUserName`). Because SYSVOL is
   broadly readable, a single read from an ordinary workstation user
   during normal business hours is lower-signal than a read from an
   unexpected host, at an unusual time, or as part of a broader SYSVOL
   enumeration pattern (many files read in a short window — consistent
   with an automated credential-hunting tool rather than a human opening
   one script).
2. The credential exposed (`svc-fileshare` in this lab) should be treated
   as compromised the moment this event fires — there's no ambiguity
   about "was it actually used," the way there sometimes is with a
   Kerberoasting ticket request. Reading the file **is** the compromise;
   proceed directly to eradication rather than waiting for confirmation
   of downstream use.
3. Check whether the exposed account has meaningful privileges. This
   lab's `svc-fileshare` is a narrow-purpose account by design, but a real
   incident should not assume that — verify group memberships and any
   delegated rights before scoping the response.

## 3. Containment, Eradication & Recovery

1. **Contain:** if there's evidence the exposed credential was actually
   used (logons by `svc-fileshare` from unexpected sources), treat that
   as a second, connected incident and follow the appropriate
   credential-misuse response for wherever it was used.
2. **Eradicate:** rotate the exposed account's password immediately. Then
   fix the actual root cause — remove the hardcoded credential from the
   script entirely (use a gMSA, a credential vault, or at minimum a
   SecureString stored outside the script) rather than just rotating the
   password and leaving the same pattern in place to be found again.
3. **Recover:** confirm whatever legitimately depends on `svc-fileshare`
   (the file share mapping this script sets up) still functions with the
   rotated credential and the fixed script.

## 4. Post-Incident Activity

- **Hardening (ties back to `docs/vulnerabilities.md` item 7):** treat
  "no hardcoded credentials in SYSVOL" as a standing audit item, not a
  one-time fix — SYSVOL scripts/GPP are a well-known, long-documented
  place this pattern recurs (this is the same underlying mistake class as
  the historical GPP `cpassword` vulnerability, just in a hand-written
  script instead of a GPP XML file).
- Since SYSVOL is broadly readable, this class of finding has an
  unusually large potential exposure window compared to most of this
  lab's other items — any domain user, at any time since the script was
  planted, could have read it. Post-incident scoping should account for
  that rather than assuming the detected read was the first one.
