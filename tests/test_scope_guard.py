"""Tests for attack/lib/scope_guard.py — the safety-critical chokepoint (docs/adr/0002).

Deliberately negative-heavy: this module's entire job is refusing things,
so most of the value here is proving the refusals actually happen, not
proving the happy path works. Every fixture writes its own lab-scope.yaml
into tmp_path rather than touching the real inventory/lab-scope.yaml, so
these tests are hermetic and don't depend on (or affect) real lab state.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
import yaml

from attack.lib.scope_guard import Host, ScopeFileError, ScopeGuard, ScopeViolation


def write_scope(tmp_path: Path, data: dict) -> Path:
    scope_file = tmp_path / "lab-scope.yaml"
    scope_file.write_text(yaml.dump(data, sort_keys=False))
    return scope_file


def base_scope(hosts: list[dict], non_attackable_roles: list[str] | None = None) -> dict:
    return {
        "version": 1,
        "lab": {"name": "test-lab", "deploy_target": "local", "provisioned": True},
        "hosts": hosts,
        "non_attackable_roles": non_attackable_roles or ["attacker", "siem"],
    }


def provisioned_host(**overrides) -> dict:
    host = {
        "id": "dc01",
        "role": "domain_controller",
        "hostname": "dc01.eadadl.lab",
        "ip": "10.42.1.4",
        "os": "windows_server",
        "provisioned": True,
    }
    host.update(overrides)
    return host


# --- Happy path -------------------------------------------------------


def test_resolves_a_provisioned_in_scope_host(tmp_path):
    scope_file = write_scope(tmp_path, base_scope([provisioned_host()]))
    guard = ScopeGuard(scope_file)

    resolved = guard.resolve_target("dc01")

    assert resolved == Host(
        id="dc01",
        role="domain_controller",
        hostname="dc01.eadadl.lab",
        ip="10.42.1.4",
        os="windows_server",
    )


def test_list_attackable_hosts_returns_only_valid_ones(tmp_path):
    scope_file = write_scope(
        tmp_path,
        base_scope(
            [
                provisioned_host(id="dc01"),
                provisioned_host(id="mem01", role="member_server"),
                provisioned_host(id="wks01_not_provisioned", provisioned=False),
                provisioned_host(id="attacker01", role="attacker"),
                provisioned_host(id="siem01", role="siem"),
            ]
        ),
    )
    guard = ScopeGuard(scope_file)

    attackable_ids = {h.id for h in guard.list_attackable_hosts()}

    assert attackable_ids == {"dc01", "mem01"}


# --- Negative cases: refused targets -----------------------------------


def test_refuses_host_not_in_scope_file(tmp_path):
    scope_file = write_scope(tmp_path, base_scope([provisioned_host(id="dc01")]))
    guard = ScopeGuard(scope_file)

    with pytest.raises(ScopeViolation, match="not present"):
        guard.resolve_target("some-host-outside-the-lab")


@pytest.mark.parametrize("role", ["attacker", "siem"])
def test_refuses_non_attackable_role_even_if_provisioned_and_has_ip(tmp_path, role):
    scope_file = write_scope(tmp_path, base_scope([provisioned_host(id="x01", role=role)]))
    guard = ScopeGuard(scope_file)

    with pytest.raises(ScopeViolation, match="non_attackable_roles"):
        guard.resolve_target("x01")


def test_refuses_unprovisioned_host(tmp_path):
    scope_file = write_scope(tmp_path, base_scope([provisioned_host(provisioned=False)]))
    guard = ScopeGuard(scope_file)

    with pytest.raises(ScopeViolation, match="not provisioned"):
        guard.resolve_target("dc01")


def test_refuses_host_missing_provisioned_field_entirely(tmp_path):
    host = provisioned_host()
    del host["provisioned"]
    # provisioned is required by the loader, so this must fail at load time,
    # not silently default to "provisioned" at resolve time.
    scope_file = write_scope(tmp_path, base_scope([host]))

    with pytest.raises(ScopeFileError, match="provisioned"):
        ScopeGuard(scope_file)


def test_refuses_provisioned_host_with_no_recorded_ip(tmp_path):
    scope_file = write_scope(tmp_path, base_scope([provisioned_host(ip=None)]))
    guard = ScopeGuard(scope_file)

    with pytest.raises(ScopeViolation, match="no recorded IP"):
        guard.resolve_target("dc01")


def test_non_attackable_role_check_beats_missing_ip_check_consistently(tmp_path):
    # Belt-and-suspenders: an attacker-role host with no IP must still be
    # refused for being non-attackable, not accidentally pass some other
    # check first. Order of checks shouldn't matter for the outcome.
    scope_file = write_scope(
        tmp_path, base_scope([provisioned_host(id="attacker01", role="attacker", ip=None)])
    )
    guard = ScopeGuard(scope_file)

    with pytest.raises(ScopeViolation):
        guard.resolve_target("attacker01")


# --- Negative cases: malformed scope file -------------------------------


def test_refuses_missing_scope_file(tmp_path):
    with pytest.raises(ScopeFileError, match="not found"):
        ScopeGuard(tmp_path / "does-not-exist.yaml")


def test_refuses_invalid_yaml(tmp_path):
    scope_file = tmp_path / "lab-scope.yaml"
    scope_file.write_text("hosts: [this is not: valid: yaml: at: all")

    with pytest.raises(ScopeFileError, match="not valid YAML"):
        ScopeGuard(scope_file)


def test_refuses_non_mapping_root(tmp_path):
    scope_file = tmp_path / "lab-scope.yaml"
    scope_file.write_text(yaml.dump(["not", "a", "mapping"]))

    with pytest.raises(ScopeFileError, match="must be a mapping"):
        ScopeGuard(scope_file)


@pytest.mark.parametrize("missing_key", ["version", "lab", "hosts"])
def test_refuses_missing_required_top_level_key(tmp_path, missing_key):
    data = base_scope([provisioned_host()])
    del data[missing_key]
    scope_file = write_scope(tmp_path, data)

    with pytest.raises(ScopeFileError, match=missing_key):
        ScopeGuard(scope_file)


def test_refuses_hosts_not_a_list(tmp_path):
    data = base_scope([provisioned_host()])
    data["hosts"] = {"dc01": provisioned_host()}
    scope_file = write_scope(tmp_path, data)

    with pytest.raises(ScopeFileError, match="must be a list"):
        ScopeGuard(scope_file)


def test_refuses_host_entry_missing_id(tmp_path):
    host = provisioned_host()
    del host["id"]
    scope_file = write_scope(tmp_path, base_scope([host]))

    with pytest.raises(ScopeFileError, match="id"):
        ScopeGuard(scope_file)


def test_refuses_duplicate_host_ids(tmp_path):
    scope_file = write_scope(tmp_path, base_scope([provisioned_host(), provisioned_host()]))

    with pytest.raises(ScopeFileError, match="duplicate"):
        ScopeGuard(scope_file)


def test_missing_non_attackable_roles_key_defaults_to_empty_not_permissive_by_accident(tmp_path):
    # non_attackable_roles is optional in the schema, but its absence must
    # not silently mean "everything is attackable" for roles that would
    # otherwise be blocked — it just means this particular scope file
    # declared no role-based restriction, which is a valid (if unusual)
    # configuration to test explicitly rather than assume.
    data = base_scope([provisioned_host(id="attacker01", role="attacker")])
    del data["non_attackable_roles"]
    scope_file = write_scope(tmp_path, data)
    guard = ScopeGuard(scope_file)

    assert guard.non_attackable_roles == frozenset()
    # With no restriction declared, this host is (correctly, per the file
    # as written) resolvable — proving the guard enforces exactly what the
    # file says, nothing more and nothing less.
    resolved = guard.resolve_target("attacker01")
    assert resolved.role == "attacker"


# --- No bypass path exists ----------------------------------------------


def test_resolve_target_signature_has_no_override_or_force_parameter():
    params = set(inspect.signature(ScopeGuard.resolve_target).parameters)
    assert params == {"self", "host_id"}, (
        "resolve_target() must only ever accept a host_id — any additional "
        "parameter is a potential bypass path and violates ADR 0002."
    )
