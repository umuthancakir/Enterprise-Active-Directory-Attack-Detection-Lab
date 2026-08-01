"""Tests for attack/runner.py — the dry-run mode is what makes this testable
in CI without a live lab (see that module's docstring).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from attack.chains import CHAINS
from attack.finding import write_run
from attack.lib.scope_guard import ScopeViolation
from attack.runner import run_scenario
from attack.techniques import TECHNIQUES


def write_scope(tmp_path: Path, *, dc_provisioned: bool = True) -> Path:
    scope_file = tmp_path / "lab-scope.yaml"
    scope_file.write_text(
        yaml.dump(
            {
                "version": 1,
                "lab": {"name": "test-lab", "deploy_target": "local", "provisioned": True},
                "hosts": [
                    {
                        "id": "dc01",
                        "role": "domain_controller",
                        "hostname": "dc01.eadadl.lab",
                        "ip": "10.42.1.4" if dc_provisioned else None,
                        "provisioned": dc_provisioned,
                    },
                    {
                        "id": "attacker01",
                        "role": "attacker",
                        "hostname": "attacker01.eadadl.lab",
                        "ip": "10.42.1.10",
                        "provisioned": True,
                    },
                ],
                "non_attackable_roles": ["attacker", "siem"],
            },
            sort_keys=False,
        )
    )
    return scope_file


# --- Registry sanity -----------------------------------------------------


def test_every_chain_only_references_known_techniques():
    for chain in CHAINS.values():
        for technique_id in chain.technique_ids:
            assert technique_id in TECHNIQUES


def test_every_technique_has_an_attack_id_and_reference_url():
    # SECURITY.md #3: every technique must map to a published ATT&CK ID.
    for technique in TECHNIQUES.values():
        assert technique.attack_id.startswith("T")
        assert technique.attack_url.startswith("https://attack.mitre.org/techniques/")


def test_every_technique_has_a_readable_fixture():
    fixtures_dir = Path(__file__).resolve().parent.parent / "attack" / "fixtures"
    for technique in TECHNIQUES.values():
        fixture = json.loads((fixtures_dir / technique.mock_fixture).read_text())
        assert "summary" in fixture
        assert "details" in fixture


# --- Dry-run mode ----------------------------------------------------------


def test_dry_run_resolves_target_and_builds_command(tmp_path):
    scope_file = write_scope(tmp_path)

    findings = run_scenario("credential_harvest", mode="dry_run", scope_file=scope_file)

    assert len(findings) == 3
    for finding in findings:
        assert finding.mode == "dry_run"
        assert finding.status == "would_run"
        assert finding.target_host_id == "dc01"
        assert finding.target_ip == "10.42.1.4"
        assert "{ip}" not in " ".join(finding.command)  # template must be fully substituted


def test_dry_run_finding_carries_the_technique_attack_id(tmp_path):
    scope_file = write_scope(tmp_path)

    findings = run_scenario("credential_harvest", mode="dry_run", scope_file=scope_file)

    by_id = {f.technique_id: f for f in findings}
    assert by_id["kerberoasting"].attack_id == "T1558.003"
    assert by_id["asrep_roasting"].attack_id == "T1558.004"


def test_domain_dominance_chain_runs_all_four_techniques_in_order(tmp_path):
    scope_file = write_scope(tmp_path)

    findings = run_scenario("domain_dominance", mode="dry_run", scope_file=scope_file)

    assert [f.technique_id for f in findings] == [
        "bloodhound_collect",
        "acl_genericall_abuse",
        "unconstrained_delegation_coerce",
        "dcsync",
    ]


# --- Safety: scope guard actually gates the runner ------------------------


def test_refuses_to_run_against_an_unprovisioned_target(tmp_path):
    scope_file = write_scope(tmp_path, dc_provisioned=False)

    with pytest.raises(ScopeViolation):
        run_scenario("credential_harvest", mode="dry_run", scope_file=scope_file)


def test_no_targets_run_when_resolution_fails_partway_through_a_chain(tmp_path, monkeypatch):
    # domain_dominance's first technique (bloodhound_collect) would resolve
    # fine, but if ANY technique in the chain can't resolve its target, the
    # whole scenario must refuse — no partial runs. Simulate this by
    # pointing at a scope file with no domain_controller at all.
    scope_file = tmp_path / "lab-scope.yaml"
    scope_file.write_text(
        yaml.dump(
            {
                "version": 1,
                "lab": {"name": "test-lab", "deploy_target": "local", "provisioned": True},
                "hosts": [],
                "non_attackable_roles": ["attacker", "siem"],
            }
        )
    )

    with pytest.raises(ScopeViolation):
        run_scenario("domain_dominance", mode="dry_run", scope_file=scope_file)


def test_unknown_scenario_raises_value_error(tmp_path):
    scope_file = write_scope(tmp_path)

    with pytest.raises(ValueError, match="Unknown scenario"):
        run_scenario("not-a-real-scenario", mode="dry_run", scope_file=scope_file)


def test_invalid_mode_raises_value_error(tmp_path):
    scope_file = write_scope(tmp_path)

    with pytest.raises(ValueError, match="mode must be"):
        run_scenario("credential_harvest", mode="not-a-real-mode", scope_file=scope_file)


# --- Persistence -----------------------------------------------------------


def test_write_run_persists_findings_as_json(tmp_path):
    scope_file = write_scope(tmp_path)
    findings = run_scenario("credential_harvest", mode="dry_run", scope_file=scope_file)

    out_path = write_run(findings, tmp_path / "results", "test-run-1")

    assert out_path.exists()
    persisted = json.loads(out_path.read_text())
    assert len(persisted) == len(findings)
    assert persisted[0]["technique_id"] == findings[0].technique_id
