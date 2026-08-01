"""Tests for config/inventory/lab_scope_inventory.py's build_inventory() —
the dynamic inventory Ansible uses, sourced from the same lab-scope.yaml
the attack engine's scope guard reads (deliberate — see that module's
docstring and docs/adr/0002-scope-guard.md).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


lab_scope_inventory = _load_module(
    REPO_ROOT / "config" / "inventory" / "lab_scope_inventory.py", "lab_scope_inventory"
)


def host(**overrides) -> dict:
    base = {
        "id": "dc01",
        "role": "domain_controller",
        "hostname": "dc01.eadadl.lab",
        "ip": "10.42.1.4",
        "provisioned": True,
    }
    base.update(overrides)
    return base


def test_unprovisioned_hosts_are_excluded_entirely():
    scope = {"hosts": [host(provisioned=False)]}

    inventory = lab_scope_inventory.build_inventory(scope)

    assert inventory["_meta"]["hostvars"] == {}
    assert "domain_controller" not in inventory


def test_hosts_with_no_ip_are_excluded_even_if_provisioned():
    scope = {"hosts": [host(ip=None)]}

    inventory = lab_scope_inventory.build_inventory(scope)

    assert inventory["_meta"]["hostvars"] == {}


def test_windows_host_gets_winrm_connection_vars():
    scope = {"hosts": [host(id="dc01", role="domain_controller")]}

    inventory = lab_scope_inventory.build_inventory(scope)

    vars_ = inventory["_meta"]["hostvars"]["dc01"]
    assert vars_["ansible_connection"] == "winrm"
    assert vars_["ansible_host"] == "10.42.1.4"
    assert "dc01" in inventory["windows"]["hosts"]
    assert "domain_controller" in inventory
    assert "dc01" in inventory["domain_controller"]["hosts"]


def test_linux_host_gets_ssh_connection_vars():
    scope = {"hosts": [host(id="attacker01", role="attacker", hostname="attacker01.eadadl.lab")]}

    inventory = lab_scope_inventory.build_inventory(scope)

    vars_ = inventory["_meta"]["hostvars"]["attacker01"]
    assert vars_["ansible_connection"] == "ssh"
    assert vars_["ansible_become"] is True
    assert "attacker01" in inventory["linux"]["hosts"]


def test_group_only_appears_when_it_has_members():
    scope = {"hosts": [host(id="dc01", role="domain_controller")]}

    inventory = lab_scope_inventory.build_inventory(scope)

    assert "member_server" not in inventory
    assert "attacker" not in inventory


def test_all_group_lists_only_non_empty_children():
    scope = {
        "hosts": [
            host(id="dc01", role="domain_controller"),
            host(id="attacker01", role="attacker", hostname="attacker01.eadadl.lab"),
        ]
    }

    inventory = lab_scope_inventory.build_inventory(scope)

    assert set(inventory["all"]["children"]) == {
        "windows",
        "linux",
        "domain_controller",
        "attacker",
    }
