#!/usr/bin/env python3
"""Sync inventory/lab-scope.yaml from `terraform output -json` in infra/azure.

This is the mechanism behind docs/adr/0002-scope-guard.md's claim that the
scope guard's allow-list tracks what's actually provisioned rather than
drifting from it. Run after `make up` (Makefile's `sync-scope` target calls
this automatically once wired up — see ROADMAP.md Phase 1).

Requires: PyYAML, and `terraform` on PATH with infra/azure already applied.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TF_DIR = REPO_ROOT / "infra" / "azure"
SCOPE_FILE = REPO_ROOT / "inventory" / "lab-scope.yaml"


def terraform_outputs() -> dict:
    result = subprocess.run(
        ["terraform", "output", "-json"],
        cwd=TF_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(
            f"terraform output failed (has `terraform apply` been run in {TF_DIR}?):\n"
            f"{result.stderr}",
            file=sys.stderr,
        )
        sys.exit(1)
    return json.loads(result.stdout)


def main() -> None:
    outputs = terraform_outputs()
    scope = yaml.safe_load(SCOPE_FILE.read_text())

    scope["lab"]["resource_group"] = outputs["resource_group_name"]["value"]
    scope["lab"]["region"] = outputs["region"]["value"]
    scope["lab"]["provisioned"] = True

    hosts_by_id = {h["id"]: h for h in scope["hosts"]}
    tf_hosts = outputs["hosts"]["value"]

    for host_id, tf_host in tf_hosts.items():
        if host_id not in hosts_by_id:
            print(
                f"WARNING: terraform output has host '{host_id}' not present in "
                f"{SCOPE_FILE} — add it manually before it can be used as a "
                "target (scope guard fails closed on unknown hosts).",
                file=sys.stderr,
            )
            continue
        hosts_by_id[host_id]["ip"] = tf_host["ip"]
        hosts_by_id[host_id]["provisioned"] = tf_host["provisioned"]

    SCOPE_FILE.write_text(yaml.dump(scope, sort_keys=False, default_flow_style=False))
    print(f"Synced {SCOPE_FILE} from terraform outputs.")


if __name__ == "__main__":
    main()
