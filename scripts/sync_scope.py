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

Requires: PyYAML.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_DIR = REPO_ROOT / "infra" / "local"
STATE_FILE = LOCAL_DIR / "state.json"
DISCOVERED_IPS_FILE = LOCAL_DIR / "discovered-ips.yaml"
SCOPE_FILE = REPO_ROOT / "inventory" / "lab-scope.yaml"


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

    scope["lab"]["deploy_target"] = "local"
    scope["lab"]["provisioned"] = True

    hosts_by_id = {h["id"]: h for h in scope["hosts"]}

    for host_id, host_state in state["hosts"].items():
        if host_id not in hosts_by_id:
            print(
                f"WARNING: infra/local state has host '{host_id}' not present "
                f"in {SCOPE_FILE} — add it manually before it can be used as "
                "a target (scope guard fails closed on unknown hosts).",
                file=sys.stderr,
            )
            continue

        ip = discovered_ips.get(host_id)
        entry = hosts_by_id[host_id]
        entry["ip"] = ip
        # A generated bundle alone doesn't mean the host is reachable —
        # require a recorded IP too, so the scope guard can't be tricked by
        # a bundle that exists but never actually booted.
        entry["provisioned"] = bool(host_state.get("provisioned") and ip)
        if ip is None:
            print(
                f"NOTE: {host_id} has no IP recorded in "
                f"{DISCOVERED_IPS_FILE} yet — marked not-provisioned in "
                f"{SCOPE_FILE} until it does.",
                file=sys.stderr,
            )

    SCOPE_FILE.write_text(yaml.dump(scope, sort_keys=False, default_flow_style=False))
    print(f"Synced {SCOPE_FILE} from {STATE_FILE} + {DISCOVERED_IPS_FILE}.")


if __name__ == "__main__":
    main()
