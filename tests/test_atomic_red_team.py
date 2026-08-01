"""Tests for attack/integrations/{atomic_red_team,atomic_runner}.py."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from attack.integrations.atomic_red_team import (
    ATOMICS_DIR,
    AtomicTest,
    load_atomic_tests_from_yaml,
    load_local_catalog,
)
from attack.integrations.atomic_runner import run_atomic_test
from attack.lib.scope_guard import ScopeViolation

# --- Parser: real ART schema -----------------------------------------------


def test_parses_a_minimal_art_schema_file(tmp_path: Path) -> None:
    yaml_path = tmp_path / "T9999.yaml"
    yaml_path.write_text(
        yaml.dump(
            {
                "attack_technique": "T9999",
                "display_name": "Fake Technique",
                "atomic_tests": [
                    {
                        "name": "Fake test",
                        "auto_generated_guid": "00000000-0000-0000-0000-000000000000",
                        "description": "A fake test.\n",
                        "supported_platforms": ["windows"],
                        "input_arguments": {
                            "target": {
                                "description": "target host",
                                "type": "string",
                                "default": "localhost",
                            }
                        },
                        "executor": {
                            "name": "command_prompt",
                            "command": "ping #{target}\n",
                        },
                    }
                ],
            }
        )
    )

    tests = load_atomic_tests_from_yaml(yaml_path)

    assert len(tests) == 1
    test = tests[0]
    assert test.technique_id == "T9999"
    assert test.test_name == "Fake test"
    assert test.input_arguments == {"target": "localhost"}
    assert test.command == "ping #{target}"


def test_render_command_substitutes_default_value() -> None:
    test = AtomicTest(
        technique_id="T9999",
        display_name="Fake",
        test_name="Fake test",
        description="",
        supported_platforms=("windows",),
        executor_name="command_prompt",
        command="net group \"#{group}\" /domain",
        input_arguments={"group": "Domain Admins"},
    )

    assert test.render_command() == 'net group "Domain Admins" /domain'


def test_render_command_override_beats_default() -> None:
    test = AtomicTest(
        technique_id="T9999",
        display_name="Fake",
        test_name="Fake test",
        description="",
        supported_platforms=("windows",),
        executor_name="command_prompt",
        command="net group \"#{group}\" /domain",
        input_arguments={"group": "Domain Admins"},
    )

    rendered = test.render_command({"group": "Enterprise Admins"})
    assert rendered == 'net group "Enterprise Admins" /domain'


def test_render_command_raises_for_missing_argument_with_no_default() -> None:
    test = AtomicTest(
        technique_id="T9999",
        display_name="Fake",
        test_name="Fake test",
        description="",
        supported_platforms=("windows",),
        executor_name="command_prompt",
        command="ping #{target}",
        input_arguments={},
    )

    with pytest.raises(KeyError):
        test.render_command()


# --- Local catalog -----------------------------------------------------


def test_local_catalog_has_three_techniques() -> None:
    catalog = load_local_catalog()
    assert set(catalog) == {"T1087.002", "T1069.002", "T1018"}


def test_every_catalog_file_matches_its_directory_naming() -> None:
    for yaml_path in ATOMICS_DIR.glob("*.yaml"):
        tests = load_atomic_tests_from_yaml(yaml_path)
        assert yaml_path.stem == tests[0].technique_id


# --- atomic_runner: same scope-guard safety as attack/runner.py -----------


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


def test_run_atomic_test_resolves_target_and_renders_command(tmp_path: Path) -> None:
    scope_file = write_scope(tmp_path)

    finding = run_atomic_test("T1087.002", scope_file=scope_file)

    assert finding.status == "would_run"
    assert finding.target_host_id == "dc01"
    assert finding.attack_id == "T1087.002"
    assert finding.command == ['net group "Domain Admins" /domain']


def test_run_atomic_test_refuses_against_unprovisioned_scope(tmp_path: Path) -> None:
    scope_file = write_scope(tmp_path, dc_provisioned=False)

    with pytest.raises(ScopeViolation):
        run_atomic_test("T1087.002", scope_file=scope_file)


def test_run_atomic_test_unknown_technique_raises_key_error(tmp_path: Path) -> None:
    scope_file = write_scope(tmp_path)

    with pytest.raises(KeyError, match="not in the local Atomic Red Team catalog"):
        run_atomic_test("T0000", scope_file=scope_file)


def test_run_atomic_test_accepts_argument_overrides(tmp_path: Path) -> None:
    scope_file = write_scope(tmp_path)

    finding = run_atomic_test(
        "T1087.002", overrides={"domain_group": "Enterprise Admins"}, scope_file=scope_file
    )

    assert finding.command == ['net group "Enterprise Admins" /domain']
