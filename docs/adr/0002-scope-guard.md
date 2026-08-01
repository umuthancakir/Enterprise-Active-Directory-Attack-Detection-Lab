# ADR 0002: Scope guard contract for attack automation

- **Status:** accepted
- **Date:** 2026-08-01

## Context

The attack scenario engine (Phase 3) executes real offensive tooling
(NetExec, Impacket, BloodHound/SharpHound, PowerView, Atomic Red Team,
Caldera). A bug, a bad default, or a copy-pasted example must not be able to
point that tooling at anything other than this lab's own hosts. This is a
hard safety requirement, not a best-effort one (see SECURITY.md #2).

## Decision

- `inventory/lab-scope.yaml` is the single, version-controlled source of
  truth for every host the attack engine is permitted to target. It records
  hostname/IP, role, and the infra-managed build artifact it corresponds to
  (see [ADR 0004](0004-revert-to-local-utm.md) for the current local
  UTM/QEMU deploy target).
- Every entry point into the attack engine (CLI runner in `attack/`, and
  later the FastAPI runner endpoint in `platform/backend/`) resolves its
  target(s) through one shared scope-guard function before invoking any
  external tool. That function loads `inventory/lab-scope.yaml`, and raises
  a hard error — refusing to run — for any target not present in it.
- There is no runtime flag, environment variable, or config option that
  bypasses the scope guard. Testing against a target outside the file
  requires editing the file (a reviewable, version-controlled change), not
  passing an override.
- The scope guard is unit tested: tests assert that an out-of-scope target is
  rejected before any subprocess/tool invocation happens, using a mocked
  executor so the test itself never shells out.
- `inventory/lab-scope.yaml` is regenerated (or diffed and reviewed) by
  `scripts/sync_scope.py` after `make up` + the manual VM-boot step (see
  `infra/local/README.md`), so the authorized list always matches what's
  actually provisioned rather than drifting from it.

## Alternatives considered

- **Allow-list passed as a CLI flag per run.** Rejected: too easy to widen
  by habit ("just this once") and not version-controlled by default.
- **Scope check inside each individual technique script.** Rejected:
  duplicated logic across every technique is exactly the kind of place a
  bypass slips in during a refactor. One shared chokepoint is easier to
  audit and to unit test exhaustively.
- **Deny-list of forbidden targets instead of an allow-list.** Rejected:
  deny-lists fail open by construction — anything not explicitly forbidden
  is allowed. An allow-list fails closed, which is the property we need.

## Consequences

- Every new technique or chain added to `attack/` must go through the shared
  scope-guard entry point; code review should treat a technique that shells
  out without going through it as a blocking issue.
- Onboarding a new lab host requires a reviewable PR-style change to
  `inventory/lab-scope.yaml`, which is the intended friction.
