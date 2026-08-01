# IR Playbooks

One playbook per detected technique, structured around
[NIST SP 800-61 Rev. 2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf)'s
four phases (Preparation; Detection & Analysis; Containment, Eradication &
Recovery; Post-Incident Activity). Each links to the specific Sigma rule,
telemetry config, and `docs/vulnerabilities.md` item it covers, rather than
being generic incident-response boilerplate.

| Playbook | Technique | ATT&CK ID | Severity |
|---|---|---|---|
| [`kerberoasting.md`](kerberoasting.md) | Kerberoasting | T1558.003 | High |
| [`asrep-roasting.md`](asrep-roasting.md) | AS-REP Roasting | T1558.004 | High |
| [`acl-abuse.md`](acl-abuse.md) | Directory ACL abuse | T1098 | Medium (context-dependent) |
| [`unconstrained-delegation.md`](unconstrained-delegation.md) | Forced-auth coercion | T1187 | High |
| [`dcsync.md`](dcsync.md) | DCSync | T1003.006 | **Critical — full domain compromise** |
| [`gpo-abuse.md`](gpo-abuse.md) | GPO edit-rights abuse | T1484.001 | High (blast radius: every linked computer) |
| [`sysvol-credential-exposure.md`](sysvol-credential-exposure.md) | SYSVOL plaintext credential read | T1552.001 | High |

`acl-abuse.md` → `unconstrained-delegation.md` → `dcsync.md` model this
lab's `domain_dominance` attack chain end to end (see
[`attack/chains.py`](../../attack/chains.py)) — read them together when
working an incident that spans more than one stage, not as independent
events. `gpo-abuse.md` and `sysvol-credential-exposure.md` correspond to
the `gpo_and_sysvol_abuse` chain instead — independent of
`domain_dominance`, since items 6/7 don't depend on items 3/4's
delegation/ACL setup.

No playbook exists yet for `bloodhound_collect` (recon) — enumeration
alone rarely warrants a full IR response; see
`ir/notebooks/` for hunting-oriented coverage of recon-stage activity
instead.

## Status

Written this session, not exercised against a real incident (no lab
exists yet — see ROADMAP.md). Every command referenced (`auditpol`,
`dsacls`, `Set-ADAccountControl`, etc.) is standard Windows/AD tooling,
not project-specific automation, so it's lower-risk than the
build-and-deploy artifacts elsewhere in this repo — but still unverified
in practice.
