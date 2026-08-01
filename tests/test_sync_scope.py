"""Tests for scripts/sync_scope.py's merge_scope() — the pure merge logic
behind `make sync-scope`. See that module's docstring for why it's split
out from file I/O specifically to make this possible.
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


sync_scope = _load_module(REPO_ROOT / "scripts" / "sync_scope.py", "sync_scope")


def base_scope() -> dict:
    return {
        "lab": {"name": "eadadl-lab", "deploy_target": "azure", "provisioned": False},
        "hosts": [
            {"id": "dc01", "role": "domain_controller", "ip": None, "provisioned": False},
            {"id": "mem01", "role": "member_server", "ip": None, "provisioned": False},
        ],
    }


def test_merges_ip_and_marks_provisioned_when_both_state_and_ip_present():
    scope = base_scope()
    state = {"hosts": {"dc01": {"provisioned": True}}}
    discovered_ips = {"dc01": "10.42.1.4"}

    updated, warnings = sync_scope.merge_scope(scope, state, discovered_ips)

    dc01 = next(h for h in updated["hosts"] if h["id"] == "dc01")
    assert dc01["ip"] == "10.42.1.4"
    assert dc01["provisioned"] is True
    assert warnings == []


def test_sets_deploy_target_and_lab_provisioned_flag():
    scope = base_scope()
    updated, _ = sync_scope.merge_scope(scope, {"hosts": {}}, {})

    assert updated["lab"]["deploy_target"] == "local"
    assert updated["lab"]["provisioned"] is True


def test_host_with_bundle_but_no_discovered_ip_stays_not_provisioned():
    # This is the important safety property: a generated .utm bundle alone
    # must never be enough to mark a host attackable — see the comment in
    # merge_scope() and docs/adr/0002-scope-guard.md.
    scope = base_scope()
    state = {"hosts": {"dc01": {"provisioned": True}}}
    discovered_ips: dict = {}  # operator hasn't recorded an IP yet

    updated, warnings = sync_scope.merge_scope(scope, state, discovered_ips)

    dc01 = next(h for h in updated["hosts"] if h["id"] == "dc01")
    assert dc01["ip"] is None
    assert dc01["provisioned"] is False
    assert any("no IP recorded" in w for w in warnings)


def test_host_with_ip_but_bundle_not_marked_provisioned_stays_not_provisioned():
    scope = base_scope()
    state = {"hosts": {"dc01": {"provisioned": False}}}
    discovered_ips = {"dc01": "10.42.1.4"}

    updated, _ = sync_scope.merge_scope(scope, state, discovered_ips)

    dc01 = next(h for h in updated["hosts"] if h["id"] == "dc01")
    assert dc01["provisioned"] is False


def test_unrelated_hosts_in_scope_are_left_untouched():
    scope = base_scope()
    state = {"hosts": {"dc01": {"provisioned": True}}}
    discovered_ips = {"dc01": "10.42.1.4"}

    updated, _ = sync_scope.merge_scope(scope, state, discovered_ips)

    mem01 = next(h for h in updated["hosts"] if h["id"] == "mem01")
    assert mem01["ip"] is None
    assert mem01["provisioned"] is False


def test_unknown_host_in_state_warns_and_does_not_crash():
    scope = base_scope()
    state = {"hosts": {"ghost01": {"provisioned": True}}}
    discovered_ips = {"ghost01": "10.42.1.99"}

    updated, warnings = sync_scope.merge_scope(scope, state, discovered_ips)

    assert {h["id"] for h in updated["hosts"]} == {"dc01", "mem01"}
    assert any("ghost01" in w and "not present" in w for w in warnings)
