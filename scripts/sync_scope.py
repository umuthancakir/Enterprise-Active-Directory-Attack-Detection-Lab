#!/usr/bin/env python3
"""Sync inventory/lab-scope.yaml from the local UTM build's state + IPs.

This is the mechanism behind docs/adr/0002-scope-guard.md's claim that the
scope guard's allow-list tracks what's actually provisioned rather than
drifting from it. For the local (UTM/QEMU) deploy target — see
docs/adr/0004-revert-to-local-utm.md — "provisioned" means
infra/local/generate_bundles.py has generated a bundle for that host, and
IPs come from infra/local/discovered-ips.yaml, which the operator fills in
by hand after each VM boots (see infra/local/README.md for why this step
isn't automated).

Run after generating bundles and recording IPs:
    python3 scripts/sync_scope.py

Requires: PyYAML. The merge logic itself (merge_scope) is pure — no file
I/O — specifically so tests/test_sync_scope.py can exercise it against
fixtures without touching the real repo state.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_DIR = REPO_ROOT / "infra" / "local"
STATE_FILE = LOCAL_DIR / "state.json"
DISCOVERED_IPS_FILE = LOCAL_DIR / "discovered-ips.yaml"
SCOPE_FILE = REPO_ROOT / "inventory" / "lab-scope.yaml"


def merge_scope(
    scope: dict[str, Any],
    state: dict[str, Any],
    discovered_ips: dict[str, str | None],
) -> tuple[dict[str, Any], list[str]]:
    """Merge infra/local build state + discovered IPs into a lab-scope.yaml document.

    Returns (updated_scope, warnings) rather than printing directly, so
    callers (main() for real use, tests for verification) control how
    warnings surface. Mutates and returns `scope` in place for convenience,
    same as the original inline implementation — callers that care about
    the input being untouched should pass a copy.
    """
    warnings: list[str] = []

    scope["lab"]["deploy_target"] = "local"
    scope["lab"]["provisioned"] = True

    hosts_by_id = {h["id"]: h for h in scope["hosts"]}

    for host_id, host_state in state["hosts"].items():
        if host_id not in hosts_by_id:
            warnings.append(
                f"infra/local state has host '{host_id}' not present in the scope "
                "file — add it manually before it can be used as a target "
                "(scope guard fails closed on unknown hosts)."
            )
            continue

        ip = discovered_ips.get(host_id)
        entry = hosts_by_id[host_id]
        entry["ip"] = ip
        # A generated bundle alone doesn't mean the host is reachable —
        # require a recorded IP too, so the scope guard can't be tricked by
        # a bundle that exists but never actually booted.
        entry["provisioned"] = bool(host_state.get("provisioned") and ip)
        # Optional — only present for hosts reached via a forwarded
        # non-22 port rather than UTM's host-only network. See
        # config/inventory/lab_scope_inventory.py's ssh_port comment.
        ssh_port = host_state.get("ssh_port")
        if ssh_port is not None:
            entry["ssh_port"] = ssh_port
        if ip is None:
            warnings.append(
                f"{host_id} has no IP recorded yet — marked not-provisioned "
                "until it does."
            )

    return scope, warnings


def main() -> None:
    if not STATE_FILE.exists():
        print(
            f"ERROR: {STATE_FILE} not found — run "
            "infra/local/generate_bundles.py first.",
            file=sys.stderr,
        )
        sys.exit(1)
    if not DISCOVERED_IPS_FILE.exists():
        print(
            f"ERROR: {DISCOVERED_IPS_FILE} not found — copy "
            f"{DISCOVERED_IPS_FILE.with_suffix('.yaml.example')} and fill in "
            "each host's IP (see infra/local/README.md).",
            file=sys.stderr,
        )
        sys.exit(1)

    state = json.loads(STATE_FILE.read_text())
    discovered_ips = yaml.safe_load(DISCOVERED_IPS_FILE.read_text()) or {}
    scope = yaml.safe_load(SCOPE_FILE.read_text())

    updated_scope, warnings = merge_scope(scope, state, discovered_ips)
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    SCOPE_FILE.write_text(yaml.dump(updated_scope, sort_keys=False, default_flow_style=False))
    print(f"Synced {SCOPE_FILE} from {STATE_FILE} + {DISCOVERED_IPS_FILE}.")


if __name__ == "__main__":
    main()
