"""Tests for ir/automation/responder.py."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from attack.lib.scope_guard import Host
from ir.automation.responder import RESPONSE_PLAYBOOK, respond_to_finding


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
                ],
                "non_attackable_roles": ["attacker", "siem"],
            }
        )
    )
    return scope_file


def test_unknown_technique_returns_no_actions(tmp_path):
    scope_file = write_scope(tmp_path)
    assert respond_to_finding("not-a-real-technique", scope_file=scope_file) == []


def test_automatable_action_resolves_target_and_builds_command(tmp_path):
    scope_file = write_scope(tmp_path)

    records = respond_to_finding("kerberoasting", scope_file=scope_file)

    assert len(records) == 1
    record = records[0]
    assert record.status == "would_run"
    assert record.target_host_id == "dc01"
    assert record.command is not None
    assert "svc-sql" in " ".join(record.command)


def test_non_automatable_action_reports_manual_required_without_a_target(tmp_path):
    scope_file = write_scope(tmp_path)

    records = respond_to_finding("dcsync", scope_file=scope_file)

    assert len(records) == 1
    record = records[0]
    assert record.status == "manual_required"
    assert record.automatable is False
    assert record.command is None
    assert record.target_host_id is None
    assert record.playbook == "ir/playbooks/dcsync.md"


def test_automatable_action_yields_nothing_when_target_unresolvable(tmp_path):
    # Fail-closed: no provisioned dc01 means no action, not a guess at
    # what host to target — same posture as attack/runner.py.
    scope_file = write_scope(tmp_path, dc_provisioned=False)

    records = respond_to_finding("kerberoasting", scope_file=scope_file)

    assert records == []


def test_every_response_action_has_a_playbook_reference():
    for actions in RESPONSE_PLAYBOOK.values():
        for action in actions:
            assert action.playbook.startswith("ir/playbooks/")


def test_non_automatable_actions_have_no_command_template():
    for actions in RESPONSE_PLAYBOOK.values():
        for action in actions:
            if not action.automatable:
                assert action.command_template is None


def test_build_command_raises_for_non_automatable_action():
    dcsync_action = RESPONSE_PLAYBOOK["dcsync"][0]
    host = Host(
        id="dc01", role="domain_controller", hostname="dc01.eadadl.lab", ip="10.42.1.4", os=""
    )
    with pytest.raises(ValueError, match="not automatable"):
        dcsync_action.build_command(host)
