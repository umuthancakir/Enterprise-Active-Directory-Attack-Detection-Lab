"""The attack scenario engine's entry point. Usage: `make attack SCENARIO=<name>`
or `python3 -m attack.runner --scenario <name> [--dry-run|--live]`.

Every target is resolved through attack.lib.scope_guard.ScopeGuard before
any tool is invoked — see docs/adr/0002-scope-guard.md. run_scenario()
resolves every technique's target up front, before running anything, so a
scenario either has all its targets available or it refuses to start at
all; there is no partial run.

Modes:
  dry_run (default) — no tool is actually invoked. Prints the exact command
    each technique would run and emits a Finding built from that
    technique's fixture in attack/fixtures/. This is what makes
    `make attack` and its tests runnable in CI without a live lab.
  live — actually invokes each technique's tool via subprocess. Gated
    entirely by the scope guard: since no host in inventory/lab-scope.yaml
    is provisioned in this environment, this path cannot run here. Not
    exercised by any test in this repo — see ROADMAP.md.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from pathlib import Path

from attack.chains import CHAINS
from attack.finding import Finding, Status, write_run
from attack.lib.scope_guard import Host, ScopeGuard, ScopeViolation
from attack.techniques import TECHNIQUES, Technique

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
RESULTS_DIR = Path(__file__).resolve().parent / "results"


def _resolve_role(guard: ScopeGuard, role: str) -> Host:
    candidates = [h for h in guard.list_attackable_hosts() if h.role == role]
    if not candidates:
        raise ScopeViolation(
            f"No attackable host with role '{role}' found in scope — refusing to run. "
            "Has `make sync-scope` been run against a provisioned lab?"
        )
    return candidates[0]


def _run_dry(technique: Technique, host: Host, command: list[str], scenario: str) -> Finding:
    fixture_path = FIXTURES_DIR / technique.mock_fixture
    fixture = json.loads(fixture_path.read_text())
    return Finding(
        scenario=scenario,
        technique_id=technique.id,
        attack_id=technique.attack_id,
        attack_url=technique.attack_url,
        target_host_id=host.id,
        target_ip=host.ip,
        tool=technique.tool,
        command=command,
        mode="dry_run",
        status="would_run",
        summary=fixture["summary"],
        raw_output=fixture["details"],
    )


def _run_live(technique: Technique, host: Host, command: list[str], scenario: str) -> Finding:
    # Not exercised by any test in this repo (no live lab exists to run
    # against) — see the module docstring and ROADMAP.md.
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    status: Status = "success" if result.returncode == 0 else "failed"
    return Finding(
        scenario=scenario,
        technique_id=technique.id,
        attack_id=technique.attack_id,
        attack_url=technique.attack_url,
        target_host_id=host.id,
        target_ip=host.ip,
        tool=technique.tool,
        command=command,
        mode="live",
        status=status,
        summary=f"{technique.tool} exited {result.returncode}",
        raw_output={"stdout": result.stdout, "stderr": result.stderr},
    )


def run_scenario(
    scenario: str,
    *,
    mode: str = "dry_run",
    scope_file: Path | str | None = None,
) -> list[Finding]:
    if scenario not in CHAINS:
        raise ValueError(f"Unknown scenario '{scenario}'. Known scenarios: {sorted(CHAINS)}")
    if mode not in ("dry_run", "live"):
        raise ValueError(f"mode must be 'dry_run' or 'live', got {mode!r}")

    chain = CHAINS[scenario]
    guard = ScopeGuard(scope_file) if scope_file is not None else ScopeGuard()

    # Resolve every target BEFORE running anything — fail closed, no
    # partial runs. See module docstring.
    resolved: dict[str, Host] = {}
    for technique_id in chain.technique_ids:
        technique = TECHNIQUES[technique_id]
        resolved[technique_id] = _resolve_role(guard, technique.target_role)

    findings: list[Finding] = []
    for technique_id in chain.technique_ids:
        technique = TECHNIQUES[technique_id]
        host = resolved[technique_id]
        command = technique.build_command(host)

        if mode == "dry_run":
            finding = _run_dry(technique, host, command, scenario)
        else:
            finding = _run_live(technique, host, command, scenario)

        findings.append(finding)

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, choices=sorted(CHAINS))
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--dry-run", action="store_true", default=True, help="default")
    mode_group.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)

    mode = "live" if args.live else "dry_run"

    try:
        findings = run_scenario(args.scenario, mode=mode)
    except ScopeViolation as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1

    for finding in findings:
        print(f"[{finding.technique_id}] ({finding.attack_id}) {finding.tool}")
        print(f"  command: {' '.join(finding.command)}")
        print(f"  {finding.status}: {finding.summary}")

    run_id = f"{args.scenario}-{uuid.uuid4().hex[:8]}"
    out_path = write_run(findings, RESULTS_DIR, run_id)
    print(f"\nWrote {len(findings)} finding(s) to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
