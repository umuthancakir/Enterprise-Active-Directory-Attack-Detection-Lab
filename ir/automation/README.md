# SOAR-style response automation

`responder.py` maps a detection hit (a `technique_id` matching
`attack/techniques.py`/`detections/sigma/`) to the concrete
containment/eradication action from the corresponding
[`ir/playbooks/`](../playbooks/) entry.

## Design

Mirrors [`attack/runner.py`](../../attack/runner.py) deliberately: every
automatable action resolves its target through the same
`attack.lib.scope_guard.ScopeGuard` that gates offensive techniques. A
password-reset or delegation-disable action against a domain controller is
exactly as consequential as an offensive technique — it gets the same
fail-closed scaffolding, not a separate, less-guarded "trusted because
it's defensive" path.

**Dry-run only — there is no live-execution mode.** Unlike
`attack/runner.py` (which has an unexercised but implemented `--live`
mode), `respond_to_finding()` never actually touches a host. Automatically
remediating a real domain without a human reviewing the specific incident
first is a deliberately unbuilt capability.

Not every response is a single command. DCSync's real remediation (krbtgt
rotated **twice**, with a replication-convergence wait between resets) is
multi-step and time-gated — modeling it as one command would imply a false
one-shot guarantee. Those actions are marked `automatable=False` and point
back to the manual playbook instead.

## Usage

```python
from ir.automation.responder import respond_to_finding

records = respond_to_finding("kerberoasting")
for r in records:
    print(r.status, r.action_id, r.command)
```

## Status

Tested — 7 passing tests in `tests/test_responder.py`, `ruff`/`mypy
--strict` clean. Never run against a real host, by design (see "Design"
above) — this is a difference from most "not run yet" caveats elsewhere in
this repo, where the gap is tooling availability rather than an
intentional scope boundary.
