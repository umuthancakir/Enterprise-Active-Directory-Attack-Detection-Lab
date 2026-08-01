"""Runs an Atomic Red Team-schema test in dry-run mode, through the exact
same scope guard as attack/runner.py — there is no separate, less-safe
path for atomic tests just because they come from a different source.
Mirrors attack/runner.py's design closely enough that its Finding schema
is reused unchanged, so an atomic-test run and a hand-modeled-technique
run look identical downstream (persistence, the platform API, etc.).

No live-execution mode exists here at all (unlike attack/runner.py's
unexercised-but-present --live) — see attack/integrations/README.md for
why.
"""

from __future__ import annotations

import argparse
import sys

from attack.finding import Finding
from attack.integrations.atomic_red_team import AtomicTest, load_local_catalog
from attack.lib.scope_guard import ScopeGuard, ScopeViolation

# Every test in the local catalog is a Windows recon command — dc01 is
# always the target, same reasoning as attack/techniques.py's module
# docstring (it's the endpoint the command actually queries).
_TARGET_ROLE = "domain_controller"


def run_atomic_test(
    technique_id: str,
    *,
    test_index: int = 0,
    overrides: dict[str, str] | None = None,
    scope_file: str | None = None,
) -> Finding:
    """Dry-run only. Raises KeyError if technique_id/test_index isn't in the
    local catalog, ScopeViolation if no attackable domain_controller resolves."""
    catalog = load_local_catalog()
    if technique_id not in catalog:
        raise KeyError(
            f"'{technique_id}' is not in the local Atomic Red Team catalog "
            f"(attack/integrations/atomics/) — known: {sorted(catalog)}"
        )
    tests = catalog[technique_id]
    if not (0 <= test_index < len(tests)):
        raise KeyError(f"'{technique_id}' has {len(tests)} test(s), no index {test_index}")
    test: AtomicTest = tests[test_index]

    guard = ScopeGuard(scope_file) if scope_file is not None else ScopeGuard()
    candidates = [h for h in guard.list_attackable_hosts() if h.role == _TARGET_ROLE]
    if not candidates:
        raise ScopeViolation(
            f"No attackable host with role '{_TARGET_ROLE}' found in scope — "
            "refusing to run atomic test."
        )
    host = candidates[0]

    rendered_command = test.render_command(overrides)

    return Finding(
        scenario=f"atomic:{technique_id}",
        technique_id=f"atomic_{technique_id}",
        attack_id=technique_id,
        attack_url=f"https://attack.mitre.org/techniques/{technique_id.replace('.', '/')}/",
        target_host_id=host.id,
        target_ip=host.ip,
        tool="Atomic Red Team (command_prompt executor)",
        command=[rendered_command],
        mode="dry_run",
        status="would_run",
        summary=f"{test.display_name}: {test.test_name}",
        raw_output={"description": test.description},
    )


def main(argv: list[str] | None = None) -> int:
    catalog = load_local_catalog()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--technique", required=True, choices=sorted(catalog))
    args = parser.parse_args(argv)

    try:
        finding = run_atomic_test(args.technique)
    except ScopeViolation as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1

    print(f"[{finding.technique_id}] ({finding.attack_id}) {finding.tool}")
    print(f"  command: {' '.join(finding.command)}")
    print(f"  {finding.status}: {finding.summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
